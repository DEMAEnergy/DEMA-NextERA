import json
import random
import numpy as np

def get_2nd_degree_approximation(data_points):
    x_values = [x for x, y in data_points]
    y_values = [y for x, y in data_points]

    # Check if y_values are all zeros to avoid fitting
    if all(y == 0 for y in y_values):
        return {"a": 0.0, "b": 0.0, "c": 0.0}

    # Fit a quadratic polynomial
    coefficients = np.polyfit(x_values, y_values, 2)
    a, b, c = coefficients
    return {"a": a, "b": b, "c": c}

def scale_heat_rate_data(heat_rate_data, scale_factor):
    return [(x * scale_factor, y) for x, y in heat_rate_data]

def create_generator(gen_id, gen_type, capacity, model):
    # Scale the heat rate data to the size of the generator
    scaled_heat_rate_data = scale_heat_rate_data(model["heat_rate_data"], capacity)
    coefficients = get_2nd_degree_approximation(scaled_heat_rate_data)
    print(scaled_heat_rate_data)
    print(coefficients)

    generator = {
        "name": f"Gen{gen_id}",
        "type": gen_type,
        "capacity_mw": round(capacity, 2),
        "coefficients": coefficients,
        "ramp_up_rate_per_hour_percent": round(random.uniform(*model["ramp_rate"]), 2),
        "ramp_down_rate_per_hour_percent": round(random.uniform(*model["ramp_rate"]), 2),
        "start_up_time_hours": round(random.uniform(*model["start_up_time"]), 2),
        "wait_time_after_shutdown_hours": round(random.uniform(*model["wait_time_after_shutdown"]), 2),
        "start_up_cost": round(random.uniform(*model["start_up_cost"]) if isinstance(model["start_up_cost"], list) else model["start_up_cost"], 2),
        "shutdown_cost": round(random.uniform(*model["shutdown_cost"]) if isinstance(model["shutdown_cost"], list) else model["shutdown_cost"], 2)
    }
    # Adjust for generators where ramp rates and times are not applicable
    if gen_type in ["SolarPV", "WindFarm"]:
        generator["ramp_up_rate_per_hour_percent"] = None
        generator["ramp_down_rate_per_hour_percent"] = None
        generator["start_up_time_hours"] = None
        generator["wait_time_after_shutdown_hours"] = None
        generator["start_up_cost"] = 0
        generator["shutdown_cost"] = 0
    return generator

def create_generators(generator_models, capacity_requirements):
    generators = []
    gen_id = 1
    for model in generator_models:
        print(model)
        gen_type = model["type"]
        required_capacity = capacity_requirements[gen_type]
        current_capacity = 0

        while current_capacity < required_capacity:
            remaining_capacity = required_capacity - current_capacity
            min_capacity = model["capacity_range"][0]
            max_capacity = min(model["capacity_range"][1], remaining_capacity)
            capacity = random.uniform(min_capacity, max_capacity)
            generator = create_generator(gen_id, gen_type, capacity, model)
            generators.append(generator)
            current_capacity += capacity
            gen_id += 1

    return generators

def main():
    # Load generator models from JSON file
    with open('Diagrams_Scripts/generator_models.json', 'r') as file:
        generator_models = json.load(file)

    # Load capacity requirements from JSON file
    with open('Diagrams_Scripts/capacity_requirements.json', 'r') as file:
        capacity_cases = json.load(file)

    # List available cases to the user
    print("Available cases:")
    for case in capacity_cases.keys():
        print(f"- {case}")

    # Prompt user to select a case
    selected_case = input("Please select a case: ")

    if selected_case not in capacity_cases:
        print("Invalid case selected. Exiting.")
        return

    capacity_requirements = capacity_cases[selected_case]

    # Create generators based on required capacities
    generators = create_generators(generator_models, capacity_requirements)

    # Output to JSON
    output = {"generators": generators}

    # Save the JSON output to a file with the selected case in the file name
    output_file_name = f'Diagrams_Scripts/generation_data_{selected_case}.json'
    with open(output_file_name, 'w') as outfile:
        json.dump(output, outfile, indent=4)

if __name__ == "__main__":
    main()