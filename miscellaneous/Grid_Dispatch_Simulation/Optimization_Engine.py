import json
import numpy as np
from scipy.optimize import linprog
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
from datetime import datetime
from ortools.linear_solver import pywraplp

# Load generation data from a JSON file
def load_generation_data(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data['generators']

# Load system load profile from a JSON file
def load_system_load_profile(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return [float(entry['MW']) for entry in data]

# Convert cost coefficients from $/MMBTU to $/BTU
def convert_coefficients(coefficients, cost_per_btu):
    cost_per_btu = cost_per_btu / 1e6  # Convert cost per MMBTU to cost per BTU
    return {key: value * cost_per_btu for key, value in coefficients.items()}

# Extract and convert coefficients for each generator
def extract_coefficients(generators, cost_per_btu_dict):
    capacities = np.array([gen['capacity_mw'] for gen in generators])
    a_coeffs = []
    b_coeffs = []
    c_coeffs = []
    types = []

    for gen in generators:
        gen_type = gen['type']
        cost_per_btu = cost_per_btu_dict[gen_type]
        converted_coeffs = convert_coefficients(gen['coefficients'], cost_per_btu)
        a_coeffs.append(converted_coeffs['a'] * 1000)  # Convert to $/MWh
        b_coeffs.append(converted_coeffs['b'] * 1000)  # Convert to $/MWh
        c_coeffs.append(converted_coeffs['c'] * 1000)  # Convert to $/MWh
        types.append(gen_type)

    return capacities, np.array(a_coeffs), np.array(b_coeffs), np.array(c_coeffs), types

# Perform piecewise linear approximation of the cost function
def piecewise_linear_approximation(a, b, c, capacity, num_segments):
    breakpoints = np.linspace(0, capacity, num_segments + 1)
    segments = len(breakpoints) - 1
    slopes = np.zeros(segments)
    intercepts = np.zeros(segments)
    
    for i in range(segments):
        x1, x2 = breakpoints[i], breakpoints[i+1]
        y1 = a * x1**2 + b * x1 + c * x1
        y2 = a * x2**2 + b * x2 + c * x2
        slopes[i] = (y2 - y1) / (x2 - x1)
        intercepts[i] = y1 - slopes[i] * x1
    
    return slopes, intercepts, breakpoints

# Optimize generation to meet the load demand with reserve margin using OR-Tools
def optimize_generation_ortools(load, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, reserve_margin_x, reserve_margin_y, flexible_load=0, flexible_load_cost=0, solar_limit=None, wind_limit=None, min_non_renewable_percentage=0):
    num_gens = len(capacities)
    solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver:
        return np.nan, {gen_type: 0 for gen_type in set(types)}, {gen_type: 0 for gen_type in set(types)}, 0, False

    # Decision variables for generation segments
    gen_vars = []
    for j in range(num_gens):
        gen_vars.append([solver.NumVar(0, capacities[j], f'gen_{j}_{k}') for k in range(num_segments)])

    # Decision variables for reserve margins
    reserve_vars = [solver.NumVar(0, solver.infinity(), f'reserve_{j}') for j in range(num_gens) if types[j] not in ['SolarPV', 'WindFarm']]

    # Decision variable for flexible load
    flexible_load_var = solver.NumVar(0, flexible_load, 'flexible_load')

    # Objective function
    objective = solver.Objective()
    for j in range(num_gens):
        slopes, intercepts, breakpoints = piecewise_linear_approximation(a_coeffs[j], b_coeffs[j], c_coeffs[j], capacities[j], num_segments)
        for k in range(num_segments):
            objective.SetCoefficient(gen_vars[j][k], slopes[k])
    # Add the flexible load cost as a negative cost (reduces system cost)
    objective.SetCoefficient(flexible_load_var, -flexible_load_cost)
    objective.SetMinimization()

    # Constraint: total generation must meet the load plus flexible load
    load_constraint = solver.Constraint(load, load)
    for j in range(num_gens):
        for k in range(num_segments):
            load_constraint.SetCoefficient(gen_vars[j][k], 1)
    load_constraint.SetCoefficient(flexible_load_var, -1)  # Subtract flexible load from the constraint

    # Constraint: reserve margin must be at least x% of total load
    reserve_margin_constraint = solver.Constraint(load * reserve_margin_x / 100, solver.infinity())
    for j in range(num_gens):
        if types[j] not in ['SolarPV', 'WindFarm']:
            reserve_margin_constraint.SetCoefficient(reserve_vars[j], 1)
    reserve_margin_constraint.SetCoefficient(flexible_load_var, 1)  # Add flexible load to the reserve margin constraint

    # Constraint: generation limits for each generator (min = 0, max = capacities[j])
    for j in range(num_gens):
        generation_limit_constraint = solver.Constraint(0, capacities[j])
        for k in range(num_segments):
            generation_limit_constraint.SetCoefficient(gen_vars[j][k], 1)

    # Add constraints for solar and wind profiles
    for j in range(num_gens):
        if types[j] == 'SolarPV' and solar_limit is not None:
            solar_constraint = solver.Constraint(0, solar_limit * capacities[j])
            for k in range(num_segments):
                solar_constraint.SetCoefficient(gen_vars[j][k], 1)
        elif types[j] == 'WindFarm' and wind_limit is not None:
            wind_constraint = solver.Constraint(0, wind_limit * capacities[j])
            for k in range(num_segments):
                wind_constraint.SetCoefficient(gen_vars[j][k], 1)

    # individual generator reserve constraints
    for j in range(num_gens):
        if types[j] not in ['SolarPV', 'WindFarm']:
            # Create a new constraint for each generator's reserve margin
            reserve_constraint = solver.Constraint(capacities[j] * reserve_margin_y / 100, solver.infinity())
            reserve_constraint.SetCoefficient(reserve_vars[j], 1)
           
            # New constraint: reserve + generation <= capacity
            reserve_generation_constraint = solver.Constraint(0, capacities[j])
            reserve_generation_constraint.SetCoefficient(reserve_vars[j], 1)
            for k in range(num_segments):
                reserve_generation_constraint.SetCoefficient(gen_vars[j][k], 1)

    # Constraint: minimum generation for non-renewable generators
    for j in range(num_gens):
        if types[j] not in ['SolarPV', 'WindFarm']:
            min_gen_constraint = solver.Constraint(capacities[j] * min_non_renewable_percentage / 100, solver.infinity())
            for k in range(num_segments):
                min_gen_constraint.SetCoefficient(gen_vars[j][k], 1)

    # Solve the problem
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        # Calculate the set point of each generator by summing its segments
        set_points = np.array([sum(gen_vars[j][k].solution_value() for k in range(num_segments)) for j in range(num_gens)])
        
        # Calculate the total dispatch for each generator type
        dispatch_total = {gen_type: 0 for gen_type in set(types)}
        for j, gen_type in enumerate(types):
            dispatch_total[gen_type] += set_points[j]
        
        # Calculate the total cost based on the original quadratic equations
        total_cost = np.sum((a_coeffs * set_points**2 + b_coeffs * set_points + c_coeffs) * set_points)
        
        # Calculate the reserves for each generator type
        reserves_by_type = {gen_type: 0 for gen_type in set(types) }
        for j, gen_type in enumerate(types):
            if gen_type not in ['SolarPV', 'WindFarm']:
                reserves_by_type[gen_type] += reserve_vars.pop(0).solution_value()
        
        # Get the system marginal cost (dual value of the load constraint)
        system_marginal_cost = load_constraint.dual_value()
        
        return total_cost, dispatch_total, reserves_by_type, flexible_load_var.solution_value(), True, system_marginal_cost
    else:
        print("Optimization failed.")
        return np.nan, {gen_type: 0 for gen_type in set(types)}, {gen_type: 0 for gen_type in set(types)}, 0, False, np.nan

# Function to select optimization method based on user input
def optimize_generation(load, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, reserve_margin_x, reserve_margin_y, flexible_load=0, flexible_load_cost=0, method='scipy', solar_limit=None, wind_limit=None, min_non_renewable_percentage=0):
    if method == 'scipy':
        return optimize_generation_scipy(load, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, reserve_margin_x, reserve_margin_y, flexible_load, solar_limit, wind_limit)
    elif method == 'ortools':
        return optimize_generation_ortools(load, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, reserve_margin_x, reserve_margin_y, flexible_load, flexible_load_cost, solar_limit, wind_limit, min_non_renewable_percentage)
    else:
        raise ValueError("Invalid optimization method. Choose 'scipy' or 'ortools'.")

# Find the system merit curve by optimizing generation for a range of loads
def find_system_merit_curve(load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, max_workers=None, reserve_margin_x=0, reserve_margin_y=0, flexible_load=0, flexible_load_cost=0, method='scipy', hourly_solar_profile=None, hourly_wind_profile=None, min_non_renewable_percentage=0):
    total_costs = [None] * len(load_profile)
    marginal_costs = np.zeros(len(load_profile))  # Initialize with an extra element
    marginal_costs[0] = 0  # Set the first element to zero
    dispatches = {gen_type: [None] * len(load_profile) for gen_type in set(types)}
    reserves = {gen_type: [None] * len(load_profile) for gen_type in set(types)}
    flexible_loads = [None] * len(load_profile)  # Initialize flexible load list

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                optimize_generation,
                load,
                capacities,
                a_coeffs,
                b_coeffs,
                c_coeffs,
                types,
                num_segments,
                reserve_margin_x,
                reserve_margin_y,
                flexible_load,
                flexible_load_cost,
                method=method,
                solar_limit=hourly_solar_profile[i] if hourly_solar_profile else None,
                wind_limit=hourly_wind_profile[i] if hourly_wind_profile else None,
                min_non_renewable_percentage=min_non_renewable_percentage
            ): i for i, load in enumerate(load_profile)
        }

        for future in as_completed(futures):
            i = futures[future]
            total_cost, dispatch_total, reserves_by_type, flexible_load_value, success, system_marginal_cost = future.result()

            if success:
                # Store the dispatch for each generator type
                for gen_type in dispatch_total:
                    dispatches[gen_type][i] = dispatch_total[gen_type]
                
                # Store the reserves for each generator type
                for gen_type in reserves_by_type:
                    reserves[gen_type][i] = reserves_by_type[gen_type]
                
                # Store the flexible load value
                flexible_loads[i] = flexible_load_value
                
                total_costs[i] = total_cost
                marginal_costs[i] = system_marginal_cost
                
                print(f"Load step {i+1}/{len(load_profile)}: Optimization successful.")
            else:
                total_costs[i] = np.nan
                print(f"Load step {i+1}/{len(load_profile)}: Optimization failed.")
                # Ensure 0 dispatch is recorded for all types in case of failure
                for gen_type in dispatches:
                    dispatches[gen_type][i] = 0
                # Ensure 0 reserves is recorded for all types in case of failure
                for gen_type in reserves:
                    reserves[gen_type][i] = 0
                # Ensure 0 flexible load is recorded in case of failure
                flexible_loads[i] = 0
                marginal_costs[i] = 0

    return total_costs, marginal_costs, dispatches, reserves, flexible_loads

# Find the dispatch for a given load profile
def find_dispatch_for_load_profile(load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, max_workers=None, reserve_margin_x=0, reserve_margin_y=0, flexible_load=0, flexible_load_cost=0, method='scipy', hourly_solar_profile=None, hourly_wind_profile=None, min_non_renewable_percentage=0):
    dispatches = {gen_type: [None] * len(load_profile) for gen_type in set(types)}
    total_costs = [None] * len(load_profile)
    marginal_costs = np.zeros(len(load_profile))  # Initialize with an extra element
    marginal_costs[0] = 0  # Set the first element to zero
    reserves = {gen_type: [None] * len(load_profile) for gen_type in set(types)}
    flexible_loads = [None] * len(load_profile)  # Initialize flexible load list

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                optimize_generation,
                load,
                capacities,
                a_coeffs,
                b_coeffs,
                c_coeffs,
                types,
                num_segments,
                reserve_margin_x,
                reserve_margin_y,
                flexible_load,
                flexible_load_cost,
                method=method,
                solar_limit=hourly_solar_profile[hour] if hourly_solar_profile else None,
                wind_limit=hourly_wind_profile[hour] if hourly_wind_profile else None,
                min_non_renewable_percentage=min_non_renewable_percentage
            ): hour for hour, load in enumerate(load_profile)
        }

        for future in as_completed(futures):
            hour = futures[future]
            total_cost, dispatch_total, reserves_by_type, flexible_load_value, success, system_marginal_cost = future.result()

            if success:
                # Store the dispatch for each generator type
                for gen_type in dispatch_total:
                    dispatches[gen_type][hour] = dispatch_total[gen_type]
                # Store the reserves for each generator type
                for gen_type in reserves_by_type:
                    reserves[gen_type][hour] = reserves_by_type[gen_type]
                # Store the flexible load value
                flexible_loads[hour] = flexible_load_value
                total_costs[hour] = total_cost
                marginal_costs[hour] = system_marginal_cost
                total_generation = sum(dispatch_total.values())
                total_reserves = sum(reserves_by_type.values())
                reserve_percentage = (total_reserves / sum(capacities)) * 100
                average_cost = total_cost / total_generation if total_generation > 0 else 0
                print(f"Hour {hour+1}/{len(load_profile)}: Optimization successful. Total Generation: {total_generation:.2f}, Total Reserves: {total_reserves:.2f}, Reserve %: {reserve_percentage:.2f}%, Flexible Load: {flexible_load_value:.2f}, Flexible Load Cost: {flexible_load_cost:.2f}, Average Cost: {average_cost:.2f}")
            else:
                total_costs[hour] = np.nan
                print(f"Hour {hour+1}/{len(load_profile)}: Optimization failed.")
                # Ensure 0 dispatch is recorded for all types in case of failure
                for gen_type in dispatches:
                    dispatches[gen_type][hour] = 0
                # Ensure 0 reserves is recorded for all types in case of failure
                for gen_type in reserves:
                    reserves[gen_type][hour] = 0
                # Ensure 0 flexible load is recorded in case of failure
                flexible_loads[hour] = 0
                marginal_costs[hour] = 0

    return total_costs, marginal_costs, dispatches, reserves, flexible_loads

# Find the optimal number of workers (threads) for parallel processing
def find_optimal_workers(load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, reserve_margin_x=0, reserve_margin_y=0, flexible_load=0, flexible_load_cost=0, method='scipy', hourly_solar_profile=None, hourly_wind_profile=None):
    best_time = float('inf')
    best_workers = None
    num_cores = os.cpu_count()

    for workers in range(1, 2 * num_cores + 1):  # Test from 1 to 2x the number of CPU cores
        start_time = time.time()
        find_system_merit_curve(load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, max_workers=workers, reserve_margin_x=reserve_margin_x, reserve_margin_y=reserve_margin_y, flexible_load=flexible_load, flexible_load_cost=flexible_load_cost, method=method, hourly_solar_profile=hourly_solar_profile, hourly_wind_profile=hourly_wind_profile)
        elapsed_time = time.time() - start_time

        print(f"Workers: {workers}, Time: {elapsed_time:.2f} seconds")

        if elapsed_time < best_time:
            best_time = elapsed_time
            best_workers = workers

    return best_workers

# Save results to a JSON file
def save_results_to_json(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Load solar profile data from a JSON file
def load_solar_profile(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

# Load wind profile data from a JSON file
def load_wind_profile(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

# Convert 5-minute interval profile data to hourly data
def convert_to_hourly(profile, key):
    hourly_profile = []
    num_intervals_per_hour = 12  # 60 minutes / 5 minutes per interval

    for i in range(0, len(profile), num_intervals_per_hour):
        hourly_data = profile[i:i + num_intervals_per_hour]
        hourly_average = np.mean([float(entry[key]) for entry in hourly_data])
        hourly_profile.append(hourly_average)

    return hourly_profile

# Create JSON structure documentation
def create_json_structure_doc(results):
    structure = {
        "functionality": "String (Merit Curve or Dispatch for Load Profile)",
        "full_run": "Boolean",
        "cost_profile": "Dictionary of cost per BTU for each generator type",
        "optimization_method": "String (scipy or ortools)",
        "flexible_load_capacity": "Float",
        "results": {
            "load_profile": "List of load values",
            "total_costs": "List of total cost values",
            "marginal_costs": "List of marginal cost values",
            "dispatches": {
                "generator_type": "List of dispatch values for each generator type"
            },
            "reserves": {
                "generator_type": "List of reserve values for each generator type"
            },
            "flexible_loads": "List of flexible load values for each hour"
        }
    }
    return structure

# Main function to run the optimization scenarios and cases
def main():
    # Prompt user to select the generator data file
    file_number = input("Enter the generator data file number (e.g., 2023 for generation_data_2023.json): ")
    filepath = f'Diagrams_Scripts/generation_data_{file_number}.json'
    
    # Check if the file exists
    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist. Terminating the program.")
        return
    
    generators = load_generation_data(filepath)
    
    # Load solar profile data
    solar_profile_path = 'Diagrams_Scripts/Solar_Profile.json'
    solar_profile = load_solar_profile(solar_profile_path)
    
    # Convert solar profile to hourly data
    hourly_solar_profile = convert_to_hourly(solar_profile, 'Solar')
    
    # Load wind profile data
    wind_profile_path = 'Diagrams_Scripts/Wind_Profile.json'
    wind_profile = load_wind_profile(wind_profile_path)
    
    # Convert wind profile to hourly data
    hourly_wind_profile = convert_to_hourly(wind_profile, 'Wind')
    
    # Define cost profiles for different scenarios
    cost_per_btu_dict_1 = {
        "GasTurbinesPlants": 1.25,
        "GasCombinedCyclePlants": 1.25,
        "CrudeOilCombinedCyclePlants": 0.6,
        "HFOCombinedCyclePlants": 0.6,
        "CrudeOilPoweredSteamTurbines": 0.6,   
        "HFOPoweredSteamTurbines": 0.6,
        "DieselGenerators": 0.6,
        "DieselPoweredSteamTurbines": 0.6,
        "SolarPV": 0.0,
        "WindFarm": 0.0
    }

    cost_per_btu_dict_2 = {
        "GasTurbinesPlants": 5,
        "GasCombinedCyclePlants": 5,
        "CrudeOilCombinedCyclePlants": 8.5,
        "HFOCombinedCyclePlants": 8.5,
        "CrudeOilPoweredSteamTurbines": 8.5,   
        "HFOPoweredSteamTurbines": 8.5,
        "DieselGenerators": 8.5,
        "DieselPoweredSteamTurbines": 8.5,
        "SolarPV": 0.0,
        "WindFarm": 0.0
    }

    cost_per_btu_dict_3 = {
        "GasTurbinesPlants": 1.25,
        "GasCombinedCyclePlants": 1.25,
        "CrudeOilCombinedCyclePlants": 13.79,
        "HFOCombinedCyclePlants": 8.9,
        "CrudeOilPoweredSteamTurbines": 13.79,   
        "HFOPoweredSteamTurbines": 8.9,
        "DieselGenerators": 8.38,
        "DieselPoweredSteamTurbines": 8.38,
        "SolarPV": 0.0,
        "WindFarm": 0.0
    }

    # Prompt user to select cost profile
    choice = input("Select cost profile (1, 2, or 3): ")
    if choice == '1':
        cost_per_btu_dict = cost_per_btu_dict_1
    elif choice == '2':
        cost_per_btu_dict = cost_per_btu_dict_2
    elif choice == '3':
        cost_per_btu_dict = cost_per_btu_dict_3
    else:
        print("Invalid choice. Defaulting to profile 1.")
        cost_per_btu_dict = cost_per_btu_dict_1

    capacities, a_coeffs, b_coeffs, c_coeffs, types = extract_coefficients(generators, cost_per_btu_dict)

    # Prompt user to select functionality
    functionality = input("Select functionality (1: Find Merit Curve, 2: Find Dispatch for Load Profile): ")
    max_workers = int(input("Enter the number of threads to use (0 for auto): "))

    # Prompt user to run full optimization or a subset
    run_full = input("Run full optimization? (y/n): ").strip().lower() == 'y'

    # Prompt user for reserve margin percentage
    reserve_margin_x = float(input("Enter the reserve margin percentage for total load (x%): "))
    reserve_margin_y = float(input("Enter the reserve margin percentage for each generator (y%): "))

    # Prompt user to select optimization method
    optimization_method = input("Select optimization method (scipy or ortools): ").strip().lower()

    # Prompt user for flexible load
    flexible_load = float(input("Enter the amount of flexible load in MW: "))

    # Prompt user for flexible load cost
    flexible_load_cost = float(input("Enter the cost of flexible load per hour (negative value to reduce system cost): "))

    # Prompt user for minimum assumed percentage for all generation other than renewable
    min_non_renewable_percentage = float(input("Enter the minimum assumed percentage for all generation other than renewable: "))

    # Prompt user to save JSON structure documentation
    save_structure_doc = input("Do you want to save a JSON file documenting the data structure? (y/n): ").strip().lower() == 'y'

    # Map functionality to descriptive names
    functionality_map = {
        '1': 'Merit Curve',
        '2': 'Dispatch for Load Profile'
    }

    results = {
        "functionality": functionality_map.get(functionality, "Unknown"),
        "full_run": run_full,
        "cost_profile": cost_per_btu_dict,
        "optimization_method": optimization_method,
        "flexible_load_capacity": flexible_load,  # Record the capacity of flexible load
        "flexible_load_cost": flexible_load_cost,  # Record the cost of flexible load
        "results": {}
    }

    # Save JSON structure documentation if requested
    if save_structure_doc:
        structure_doc = create_json_structure_doc(results)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        structure_filename = f"./Simulation_Results/results_structure_{timestamp}.json"
        save_results_to_json(structure_filename, structure_doc)
        print(f"JSON structure documentation saved to {structure_filename}")

    if max_workers == 0:
        if functionality == '1':
            load_steps = 100
            max_load = capacities.sum()
            load_profile = np.linspace(0, max_load, load_steps)

            if not run_full:
                load_profile = load_profile[:int(len(load_profile) * 0.05)]

            # Define number of segments for piecewise linear approximation
            num_segments = 10

            # Find the optimal number of workers
            best_workers = find_optimal_workers(load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, reserve_margin_x=reserve_margin_x, reserve_margin_y=reserve_margin_y, flexible_load=flexible_load, flexible_load_cost=flexible_load_cost, method=optimization_method, hourly_solar_profile=hourly_solar_profile, hourly_wind_profile=hourly_wind_profile)
            print(f"Optimal number of workers: {best_workers}")

            total_costs, marginal_costs, dispatches, reserves, flexible_loads = find_system_merit_curve(
                load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, 
                max_workers=best_workers, reserve_margin_x=reserve_margin_x, reserve_margin_y=reserve_margin_y, 
                flexible_load=flexible_load, flexible_load_cost=flexible_load_cost, method=optimization_method, 
                hourly_solar_profile=hourly_solar_profile, hourly_wind_profile=hourly_wind_profile,
                min_non_renewable_percentage=min_non_renewable_percentage
            )

            results["results"] = {
                "load_profile": load_profile.tolist(),
                "total_costs": total_costs,
                "marginal_costs": marginal_costs.tolist(),
                "dispatches": {gen_type: np.array(dispatch).tolist() for gen_type, dispatch in dispatches.items()},
                "reserves": {gen_type: np.array(reserve).tolist() for gen_type, reserve in reserves.items()},
                "flexible_loads": flexible_loads  # Record the flexible load values
            }

        elif functionality == '2':
            load_profile_filepath = 'Diagrams_Scripts/system_load_profile.json'
            load_profile = load_system_load_profile(load_profile_filepath)

            if not run_full:
                load_profile = load_profile[:int(24*30)]

            # Define number of segments for piecewise linear approximation
            num_segments = 10

            # Find the optimal number of workers
            best_workers = find_optimal_workers(load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, reserve_margin_x=reserve_margin_x, reserve_margin_y=reserve_margin_y, flexible_load=flexible_load, flexible_load_cost=flexible_load_cost, method=optimization_method, hourly_solar_profile=hourly_solar_profile, hourly_wind_profile=hourly_wind_profile)
            print(f"Optimal number of workers: {best_workers}")

            total_costs, marginal_costs, dispatches, reserves, flexible_loads = find_dispatch_for_load_profile(
                load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, 
                max_workers=best_workers, reserve_margin_x=reserve_margin_x, reserve_margin_y=reserve_margin_y, 
                flexible_load=flexible_load, flexible_load_cost=flexible_load_cost, method=optimization_method, 
                hourly_solar_profile=hourly_solar_profile, hourly_wind_profile=hourly_wind_profile,
                min_non_renewable_percentage=min_non_renewable_percentage
            )

            results["results"] = {
                "load_profile": load_profile,
                "total_costs": total_costs,
                "marginal_costs": marginal_costs.tolist(),
                "dispatches": {gen_type: np.array(dispatch).tolist() for gen_type, dispatch in dispatches.items()},
                "reserves": {gen_type: np.array(reserve).tolist() for gen_type, reserve in reserves.items()},
                "flexible_loads": flexible_loads  # Record the flexible load values
            }

    else:
        if functionality == '1':
            load_steps = 100
            max_load = capacities.sum()
            load_profile = np.linspace(0, max_load, load_steps)

            if not run_full:
                load_profile = load_profile[:int(len(load_profile) * 0.05)]

            # Define number of segments for piecewise linear approximation
            num_segments = 10

            total_costs, marginal_costs, dispatches, reserves, flexible_loads = find_system_merit_curve(
                load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, 
                max_workers=max_workers, reserve_margin_x=reserve_margin_x, reserve_margin_y=reserve_margin_y, 
                flexible_load=flexible_load, flexible_load_cost=flexible_load_cost, method=optimization_method, 
                hourly_solar_profile=hourly_solar_profile, hourly_wind_profile=hourly_wind_profile,
                min_non_renewable_percentage=min_non_renewable_percentage
            )

            results["results"] = {
                "load_profile": load_profile.tolist(),
                "total_costs": total_costs,
                "marginal_costs": marginal_costs.tolist(),
                "dispatches": {gen_type: np.array(dispatch).tolist() for gen_type, dispatch in dispatches.items()},
                "reserves": {gen_type: np.array(reserve).tolist() for gen_type, reserve in reserves.items()},
                "flexible_loads": flexible_loads  # Record the flexible load values
            }

        elif functionality == '2':
            load_profile_filepath = 'Diagrams_Scripts/system_load_profile.json'
            load_profile = load_system_load_profile(load_profile_filepath)

            if not run_full:
                load_profile = load_profile[:int(len(load_profile) * 0.05)]

            # Define number of segments for piecewise linear approximation
            num_segments = 10

            total_costs, marginal_costs, dispatches, reserves, flexible_loads = find_dispatch_for_load_profile(
                load_profile, capacities, a_coeffs, b_coeffs, c_coeffs, types, num_segments, 
                max_workers=max_workers, reserve_margin_x=reserve_margin_x, reserve_margin_y=reserve_margin_y, 
                flexible_load=flexible_load, flexible_load_cost=flexible_load_cost, method=optimization_method, 
                hourly_solar_profile=hourly_solar_profile, hourly_wind_profile=hourly_wind_profile,
                min_non_renewable_percentage=min_non_renewable_percentage
            )

            results["results"] = {
                "load_profile": load_profile,
                "total_costs": total_costs,
                "marginal_costs": marginal_costs.tolist(),
                "dispatches": {gen_type: np.array(dispatch).tolist() for gen_type, dispatch in dispatches.items()},
                "reserves": {gen_type: np.array(reserve).tolist() for gen_type, reserve in reserves.items()},
                "flexible_loads": flexible_loads  # Record the flexible load values
            }

    # Ensure the directory exists
    os.makedirs('./Simulation_Results', exist_ok=True)

    # Save results to JSON file with a timestamp in the name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"./Simulation_Results/results_{timestamp}.json"
    save_results_to_json(filename, results)

if __name__ == "__main__":
    main()