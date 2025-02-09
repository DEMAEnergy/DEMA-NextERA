import json
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd  # Add pandas for table display
import random  # Add import for random
from matplotlib.animation import FuncAnimation
from scipy.interpolate import make_interp_spline

# Load results from a JSON file
def load_results_from_json(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

# Plot the merit curve and marginal cost
def plot_merit_curve_and_marginal_cost(load_profile, total_costs, marginal_costs):
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(load_profile, total_costs, label='Total Cost', color='blue')
    ax1.set_xlabel('System Load (MW)')
    ax1.set_ylabel('Total Cost ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(load_profile, marginal_costs, label='Marginal Cost', color='red')
    ax2.set_ylabel('Marginal Cost ($/MWh)')
    ax2.legend(loc='upper right')

    plt.title('Merit Curve and Marginal Cost of the System')
    plt.show()

# Plot total cost, marginal cost, and average cost vs hours
def plot_total_marginal_and_average_cost_vs_hours(load_profile, total_costs, marginal_costs):
    hours = np.arange(len(load_profile))
    average_costs = np.divide(total_costs, load_profile, out=np.zeros_like(total_costs), where=load_profile!=0)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(hours, total_costs, label='Total Cost', color='blue')
    ax1.set_xlabel('Hour of the Year')
    ax1.set_ylabel('Total Cost ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(hours, marginal_costs, label='Marginal Cost', color='red')
    ax2.plot(hours, average_costs, label='Average Cost', color='green')
    ax2.set_ylabel('Cost ($/MWh)')
    ax2.legend(loc='upper right')

    plt.title('Total Cost, Marginal Cost, and Average Cost vs Hour of the Year')
    plt.show()

# Plot the dispatch for a given load profile
def plot_dispatch_for_load_profile(load_profile, dispatches):
    fig, ax = plt.subplots(figsize=(10, 6))
    hours = np.arange(len(load_profile))

    # Define the order and colors for each generation type
    gen_order = [
        "GasTurbinesPlants", "GasCombinedCyclePlants", "CrudeOilCombinedCyclePlants",
        "HFOCombinedCyclePlants", "CrudeOilPoweredSteamTurbines", "HFOPoweredSteamTurbines",
        "DieselGenerators", "DieselPoweredSteamTurbines", "SolarPV", "WindFarm"
    ]
    colors = {
        "GasTurbinesPlants": "blue",
        "GasCombinedCyclePlants": "green",
        "CrudeOilCombinedCyclePlants": "red",
        "HFOCombinedCyclePlants": "purple",
        "CrudeOilPoweredSteamTurbines": "orange",
        "HFOPoweredSteamTurbines": "brown",
        "DieselGenerators": "pink",
        "DieselPoweredSteamTurbines": "gray",
        "SolarPV": "yellow",
        "WindFarm": "cyan"
    }

    # Prepare data for stacked area plot in the defined order
    dispatch_array = np.array([dispatches[gen_type] for gen_type in gen_order])
    labels = gen_order
    color_list = [colors[gen_type] for gen_type in gen_order]

    ax.stackplot(hours, dispatch_array, labels=labels, colors=color_list)

    ax.set_xlabel('Hour of the Year')
    ax.set_ylabel('Dispatch (MW)')
    ax.legend(loc='upper left')
    plt.title('Dispatch per Type of Generation vs Hour of the Year (Stacked Area)')
    plt.show()

# Get the latest JSON file based on the timestamp in the filename
def get_latest_json_file(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.json')]
    if not files:
        return None
    latest_file = max(files, key=lambda x: datetime.strptime(x.split('_')[-1].split('.')[0], "%Y%m%d%H%M%S"))
    return os.path.join(directory, latest_file)

# Plot total cost and average cost vs hours (without marginal cost)
def plot_total_and_average_cost_vs_hours(load_profile, total_costs):
    hours = np.arange(len(load_profile))
    average_costs = np.divide(total_costs, load_profile, out=np.zeros_like(total_costs), where=load_profile!=0)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(hours, total_costs, label='Total Cost', color='blue')
    ax1.set_xlabel('Hour of the Year')
    ax1.set_ylabel('Total Cost ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(hours, average_costs, label='Average Cost', color='green')
    ax2.set_ylabel('Cost ($/MWh)')
    ax2.legend(loc='upper right')

    plt.title('Total Cost and Average Cost vs Hour of the Year')
    plt.show()

# Plot total cost and average cost vs days (daily averages)
def plot_daily_total_and_average_cost(load_profile, total_costs):
    days = np.arange(len(load_profile) // 24)
    daily_total_costs = np.add.reduceat(total_costs, np.arange(0, len(total_costs), 24))
    daily_load_profile = np.add.reduceat(load_profile, np.arange(0, len(load_profile), 24))
    daily_average_costs = np.divide(daily_total_costs, daily_load_profile, out=np.zeros_like(daily_total_costs), where=daily_load_profile!=0)
    
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(days, daily_total_costs, label='Daily Total Cost', color='blue')
    ax1.set_xlabel('Day of the Year')
    ax1.set_ylabel('Total Cost ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(days, daily_average_costs, label='Daily Average Cost', color='green')
    ax2.set_ylabel('Cost ($/MWh)')
    ax2.legend(loc='upper right')

    plt.title('Daily Total Cost and Average Cost vs Day of the Year')
    plt.show()

# Plot wind and solar dispatch
def plot_wind_and_solar_dispatch(load_profile, dispatches):
    fig, ax = plt.subplots(figsize=(10, 6))
    hours = np.arange(len(load_profile))

    # Define the order and colors for wind and solar generation
    gen_order = ["SolarPV", "WindFarm"]
    colors = {
        "SolarPV": "yellow",
        "WindFarm": "cyan"
    }

    # Prepare data for stacked area plot in the defined order
    dispatch_array = np.array([dispatches[gen_type] for gen_type in gen_order])
    labels = gen_order
    color_list = [colors[gen_type] for gen_type in gen_order]

    ax.stackplot(hours, dispatch_array, labels=labels, colors=color_list)

    ax.set_xlabel('Hour of the Year')
    ax.set_ylabel('Dispatch (MW)')
    ax.legend(loc='upper left')
    plt.title('Wind and Solar Dispatch vs Hour of the Year (Stacked Area)')
    plt.show()

# Load timing definitions from a JSON file
def load_timing_definitions(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

# Calculate average $/MWh price for each group for all months
def calculate_average_prices_for_all_months(load_profile, total_costs, timing_definitions):
    hours_in_month = {
        "January": 31 * 24,
        "February": 28 * 24,
        "March": 31 * 24,
        "April": 30 * 24,
        "May": 31 * 24,
        "June": 30 * 24,
        "July": 31 * 24,
        "August": 31 * 24,
        "September": 30 * 24,
        "October": 31 * 24,
        "November": 30 * 24,
        "December": 31 * 24
    }

    month_start_hour = 0
    results = {month: {"Peak": 0, "Off-peak": 0, "Shoulder": 0} for month in hours_in_month.keys()}
    counts = {month: {"Peak": 0, "Off-peak": 0, "Shoulder": 0} for month in hours_in_month.keys()}

    for month, hours in hours_in_month.items():
        for hour in range(month_start_hour, month_start_hour + hours):
            hour_of_day = hour % 24
            group = next((period["Group"] for period in timing_definitions[month] if int(period["Hours"].split(" - ")[0].split(":")[0]) == hour_of_day), None)
            if group:
                results[month][group] += total_costs[hour] / load_profile[hour] if load_profile[hour] != 0 else 0
                counts[month][group] += 1
        month_start_hour += hours

    average_prices = {month: {group: results[month][group] / counts[month][group] if counts[month][group] != 0 else 0 for group in results[month]} for month in results}
    return average_prices

# Calculate weekly maximum load
def calculate_weekly_max_load(load_profile):
    weeks = len(load_profile) // (7 * 24)
    weekly_max_load = [max(load_profile[i * 7 * 24:(i + 1) * 7 * 24]) for i in range(weeks)]
    return weekly_max_load

# Plot weekly maximum load
def plot_weekly_max_load(weekly_max_load):
    weeks = np.arange(1, len(weekly_max_load) + 1)
    plt.figure(figsize=(10, 6))
    plt.plot(weeks, weekly_max_load, marker='o', linestyle='-', color='b')
    plt.xlabel('Week')
    plt.ylabel('Maximum Load (MW)')
    plt.title('Weekly Maximum Load')
    plt.grid(True)
    plt.show()

def scale_dispatches_uniformly(dispatches, scaling_factor):
    """Scales all dispatch values uniformly by a scaling_factor."""
    scaled_dispatches = {}
    for plant_type, values in dispatches.items():
        scaled_dispatches[plant_type] = [value * scaling_factor for value in values]
    return scaled_dispatches

def scale_dispatches_randomly(dispatches, min_percentage, max_percentage):
    """Scales each dispatch value randomly by a percentage between min_percentage and max_percentage."""
    scaled_dispatches = {}
    for plant_type, values in dispatches.items():
        scaled_dispatches[plant_type] = [
            value * random.uniform(min_percentage / 100, max_percentage / 100) for value in values
        ]
    return scaled_dispatches

# Update the save_json function
def save_json(data, filename):
    # Extract the base name without the timestamp
    base_name = filename.split('_')[0]
    
    # Generate a new timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create the new filename with the updated timestamp
    new_filename = f"{base_name}_{timestamp}.json"
    
    # Save the JSON data
    with open(os.path.join('Simulation_Results', new_filename), 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved optimized data to {new_filename}")

# Add this new function for the animated load profile
def animate_load_profile(load_profile, dispatches, reserves, flexible_loads, categorized_dispatches):
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3)
    
    ax1 = fig.add_subplot(gs[0, :])  # Full year plot
    ax2 = fig.add_subplot(gs[1, 0])  # Bar chart plot
    ax3 = fig.add_subplot(gs[1, 1])  # Generator dispatch by technology
    ax4 = fig.add_subplot(gs[1, 2])  # Generator dispatch by fuel

    hours = np.arange(len(load_profile))
    window_size = 25  # 12 hours before + current hour + 12 hours after

    # Smooth the load profile for the full year plot
    smooth_hours = np.linspace(0, len(load_profile) - 1, len(load_profile) * 10)
    smooth_load = make_interp_spline(hours, load_profile)(smooth_hours)
    smooth_flexible_load = make_interp_spline(hours, flexible_loads)(smooth_hours)

    # Full year plot
    line_full, = ax1.plot(smooth_hours, smooth_load, lw=1, color='#1f77b4', label='Load Profile')
    ax1.set_xlim(0, len(load_profile) - 1)
    ax1.set_ylim(min(load_profile) * 0.9, max(load_profile) * 1.1)
    ax1.set_title('Full Year Load Profile', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Hours of the Year', fontsize=10)
    ax1.set_ylabel('Load (MW)', fontsize=10)
    vertical_line = ax1.axvline(x=0, color='r', linestyle='--')

    ax1_flex = ax1.twinx()
    line_flex_full, = ax1_flex.plot(smooth_hours, smooth_flexible_load, lw=1, color='orange', label='Flexible Load')
    ax1_flex.set_ylabel('Flexible Load (MW)', fontsize=10)

    # Bar chart plot
    bar_total_load = ax2.bar(['Total Load'], [0], color='#1f77b4', label='Total Load')
    bar_total_gen = ax2.bar(['Total Generation'], [0], color='green', label='Total Generation')
    bar_total_gen_reserve = ax2.bar(['Total Generation Reserve'], [0], color='red', label='Total Generation Reserve')
    bar_total_load_reserve = ax2.bar(['Total Load Reserve'], [0], color='orange', label='Total Load Reserve')
    ax2.set_ylim(0, max(load_profile) * 1.2)
    ax2.set_title('Total Load, Generation, and Reserves', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Power (MW)', fontsize=10)
    ax2.set_xticklabels(['Total Load', 'Total Generation', 'Total Generation Reserve', 'Total Load Reserve'], rotation=45, ha='right')
    ax2.legend()

    # Generator dispatch by technology
    tech_order = list(categorized_dispatches["technology"].keys())
    tech_colors = plt.cm.tab20(np.linspace(0, 1, len(tech_order)))
    tech_bars = {tech: ax3.bar([tech], [0], color=tech_colors[i]) for i, tech in enumerate(tech_order)}
    ax3.set_ylim(0, max([max(categorized_dispatches["technology"][tech]) for tech in tech_order]) * 1.2)
    ax3.set_title('Dispatch by Technology', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Technology', fontsize=10)
    ax3.set_ylabel('Power (MW)', fontsize=10)
    ax3.set_xticklabels(tech_order, rotation=45, ha='right')
    ax3.legend()

    # Generator dispatch by fuel
    fuel_order = list(categorized_dispatches["fuel"].keys())
    fuel_colors = plt.cm.tab20(np.linspace(0, 1, len(fuel_order)))
    fuel_bars = {fuel: ax4.bar([fuel], [0], color=fuel_colors[i]) for i, fuel in enumerate(fuel_order)}
    ax4.set_ylim(0, max([max(categorized_dispatches["fuel"][fuel]) for fuel in fuel_order]) * 1.2)
    ax4.set_title('Dispatch by Fuel', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Fuel', fontsize=10)
    ax4.set_ylabel('Power (MW)', fontsize=10)
    ax4.set_xticklabels(fuel_order, rotation=45, ha='right')
    ax4.legend()

    def init():
        for bar in tech_bars.values():
            bar[0].set_height(0)
        for bar in fuel_bars.values():
            bar[0].set_height(0)
        bar_total_load[0].set_height(0)
        bar_total_gen[0].set_height(0)
        bar_total_gen_reserve[0].set_height(0)
        bar_total_load_reserve[0].set_height(0)
        return [bar[0] for bar in tech_bars.values()] + [bar[0] for bar in fuel_bars.values()] + [bar_total_load[0], bar_total_gen[0], bar_total_gen_reserve[0], bar_total_load_reserve[0]]

    def update(frame):
        vertical_line.set_xdata(frame)

        total_gen = sum(dispatches[gen_type][frame] for gen_type in dispatches)
        total_gen_reserve = sum(reserves[gen_type][frame] for gen_type in reserves)
        bar_total_load[0].set_height(max(0, load_profile[frame] + flexible_loads[frame]))
        bar_total_gen[0].set_height(max(0, total_gen))
        bar_total_gen_reserve[0].set_height(max(0, total_gen_reserve))
        bar_total_load_reserve[0].set_height(max(0, flexible_loads[frame]))

        for tech, bar in tech_bars.items():
            bar[0].set_height(max(0, categorized_dispatches["technology"][tech][frame]))
        for fuel, bar in fuel_bars.items():
            bar[0].set_height(max(0, categorized_dispatches["fuel"][fuel][frame]))

        return [vertical_line] + [bar[0] for bar in tech_bars.values()] + [bar[0] for bar in fuel_bars.values()] + [bar_total_load[0], bar_total_gen[0], bar_total_gen_reserve[0], bar_total_load_reserve[0]]

    try:
        ani = FuncAnimation(fig, update, frames=len(load_profile),
                            init_func=init, blit=True, interval=1)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"An error occurred during animation: {e}")

# Define the mapping of generation types to technology and fuel
generation_mapping = {
    "GasTurbinesPlants": {"technology": "Simple Cycle", "fuel": "Natural Gas"},
    "GasCombinedCyclePlants": {"technology": "Combined Cycle", "fuel": "Natural Gas"},
    "CrudeOilCombinedCyclePlants": {"technology": "Combined Cycle", "fuel": "Crude Oil"},
    "HFOCombinedCyclePlants": {"technology": "Combined Cycle", "fuel": "HFO"},
    "CrudeOilPoweredSteamTurbines": {"technology": "Steam Turbines", "fuel": "Crude Oil"},
    "HFOPoweredSteamTurbines": {"technology": "Steam Turbines", "fuel": "HFO"},
    "DieselGenerators": {"technology": "Simple Cycle", "fuel": "Diesel"},
    "DieselPoweredSteamTurbines": {"technology": "Steam Turbines", "fuel": "Diesel"},
    "SolarPV": {"technology": "Renewable Energy", "fuel": "Renewable Energy"},
    "WindFarm": {"technology": "Renewable Energy", "fuel": "Renewable Energy"}
}

# Function to categorize dispatches by technology and fuel
def categorize_dispatches(dispatches):
    categorized_dispatches = {
        "technology": {tech: np.zeros(len(next(iter(dispatches.values())))) for tech in set(v["technology"] for v in generation_mapping.values())},
        "fuel": {fuel: np.zeros(len(next(iter(dispatches.values())))) for fuel in set(v["fuel"] for v in generation_mapping.values())}
    }
    print(categorized_dispatches)

    for gen_type, values in dispatches.items():
        tech = generation_mapping[gen_type]["technology"]
        fuel = generation_mapping[gen_type]["fuel"]
        categorized_dispatches["technology"][tech] += np.array(values)
        categorized_dispatches["fuel"][fuel] += np.array(values)

    print(categorized_dispatches)
    return categorized_dispatches

def analyze_system_cost(results):
    total_system_cost = np.sum(results["total_costs"])
    total_twh_served = np.sum(results["load_profile"]) / 1e6  # Convert MWh to TWh
    average_system_cost = total_system_cost / (total_twh_served * 1e6) if total_twh_served != 0 else 0  # Calculate average cost per MWh

    # Calculate capacity utilization
    total_capacity = sum([max(dispatch) for dispatch in results["dispatches"].values()])
    capacity_utilization = total_twh_served / (total_capacity * 8760) if total_capacity != 0 else 0

    # Calculate curtailment of renewable energy
    renewable_types = ["SolarPV", "WindFarm"]
    total_renewable_generation = sum([np.sum(results["dispatches"][gen_type]) for gen_type in renewable_types])
    total_possible_renewable_generation = sum([max(results["dispatches"][gen_type]) * 8760 for gen_type in renewable_types])
    curtailment = (total_possible_renewable_generation - total_renewable_generation) / total_possible_renewable_generation if total_possible_renewable_generation != 0 else 0

    # List quantities of fuel used by type
    fuel_quantities = {fuel: 0 for fuel in set(v["fuel"] for v in generation_mapping.values())}
    for gen_type, values in results["dispatches"].items():
        fuel = generation_mapping[gen_type]["fuel"]
        fuel_quantities[fuel] += np.sum(values)
    # Print the results as a table
    print("\nSystem Cost Analysis:")
    print(f"{'Metric':<40} {'Value':<20}")
    print(f"{'-'*40} {'-'*20}")
    print(f"{'Total System Cost ($)':<40} {total_system_cost:>20,.2f}")
    print(f"{'Total TWh Served':<40} {total_twh_served:>20,.2f}")
    print(f"{'Average System Cost ($/MWh)':<40} {average_system_cost:>20,.2f}")
    print(f"{'Capacity Utilization (%)':<40} {capacity_utilization * 100:>20,.2f}")
    print(f"{'Curtailment of Renewable Energy (%)':<40} {curtailment * 100:>20,.2f}")
    print(f"{'Fuel Quantities (MWh)':<40}")
    for fuel, quantity in fuel_quantities.items():
        print(f"  {fuel:<38} {quantity:>20,.2f}")

# Main function to handle user interaction
def main():
    directory = './Simulation_Results'
    timing_filepath = './Diagrams_Scripts/BSC_Saudi_Timing.json'
    timing_definitions = load_timing_definitions(timing_filepath)

    print("Select JSON file to load:")
    print("1. Select a specific file")
    print("2. Load the latest file")

    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == '1':
        files = [f for f in os.listdir(directory) if f.endswith('.json')]
        if not files:
            print("No JSON files found in the directory.")
            return

        for i, file in enumerate(files):
            print(f"{i + 1}. {file}")

        file_choice = int(input("Enter the number of the file to load: ").strip())
        if file_choice < 1 or file_choice > len(files):
            print("Invalid choice.")
            return

        filepath = os.path.join(directory, files[file_choice - 1])
    elif choice == '2':
        filepath = get_latest_json_file(directory)
        if not filepath:
            print("No JSON files found in the directory.")
            return
    else:
        print("Invalid choice.")
        return

    data = load_results_from_json(filepath)
    results = data["results"]

    print("Select plot to display:")
    print("1. Merit Curve and Marginal Cost")
    print("2. Total Cost, Marginal Cost, and Average Cost vs Hour of the Year")
    print("3. Total Cost and Average Cost vs Hour of the Year (without Marginal Cost)")
    print("4. Dispatch per Type of Generation vs Hour of the Year (Stacked Area)")
    print("5. Daily Total Cost and Average Cost vs Day of the Year (Daily Averages)")
    print("6. Wind and Solar Dispatch vs Hour of the Year (Stacked Area)")
    print("7. Calculate average $/MWh price for each group in a month")
    print("8. Plot weekly maximum load")
    print("9. Scale dispatches")
    print("10. Animate Load Profile")
    print("11. Analyze System Cost")

    plot_choice = input("Enter your choice (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, or 11): ").strip()

    if plot_choice == '1':
        plot_merit_curve_and_marginal_cost(results["load_profile"], results["total_costs"], results["marginal_costs"])
    elif plot_choice == '2':
        plot_total_marginal_and_average_cost_vs_hours(results["load_profile"], results["total_costs"], results["marginal_costs"])
    elif plot_choice == '3':
        plot_total_and_average_cost_vs_hours(results["load_profile"], results["total_costs"])
    elif plot_choice == '4':
        if "load_profile" in results:
            plot_dispatch_for_load_profile(results["load_profile"], results["dispatches"])
        else:
            print("Load profile data not available in the selected JSON file.")
    elif plot_choice == '5':
        plot_daily_total_and_average_cost(results["load_profile"], results["total_costs"])
    elif plot_choice == '6':
        plot_wind_and_solar_dispatch(results["load_profile"], results["dispatches"])
    elif plot_choice == '7':
        average_prices_all_months = calculate_average_prices_for_all_months(results["load_profile"], results["total_costs"], timing_definitions)
        df = pd.DataFrame(average_prices_all_months).T  # Transpose to get months as rows
        print(df)
    elif plot_choice == '8':
        weekly_max_load = calculate_weekly_max_load(results["load_profile"])
        plot_weekly_max_load(weekly_max_load)
    elif plot_choice == '9':
        print("Select scaling method:")
        print("1. Uniform scaling")
        print("2. Random scaling")

        scaling_choice = input("Enter your choice (1 or 2): ").strip()

        if scaling_choice == '1':
            scaling_factor = float(input("Enter the scaling factor (e.g., 1.2 for 20% increase): ").strip())
            scaled_dispatches = scale_dispatches_uniformly(results["dispatches"], scaling_factor)
        elif scaling_choice == '2':
            min_percentage = float(input("Enter the minimum percentage (e.g., 90 for 90%): ").strip())
            max_percentage = float(input("Enter the maximum percentage (e.g., 110 for 110%): ").strip())
            scaled_dispatches = scale_dispatches_randomly(results["dispatches"], min_percentage, max_percentage)
        else:
            print("Invalid choice.")
            return

        # Update the JSON data with scaled dispatches
        results["dispatches"] = scaled_dispatches

        # Save the scaled data back to a new JSON file in the same directory
        directory, filename = os.path.split(filepath)
        save_json(data, filename)
    elif plot_choice == '10':
        if "reserves" in results and "flexible_loads" in results:
            categorized_dispatches = categorize_dispatches(results["dispatches"])
            animate_load_profile(results["load_profile"], results["dispatches"], results["reserves"], results["flexible_loads"], categorized_dispatches)
        else:
            print("Reserves or flexible loads data not available in the JSON file. Please check the file structure.")
            return
    elif plot_choice == '11':
        analyze_system_cost(results)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()