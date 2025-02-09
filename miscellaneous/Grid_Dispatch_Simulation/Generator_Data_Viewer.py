import json
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

# Load generator data from JSON file
def load_generators(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data['generators']

# Find generator by name
def find_generator(generators, name):
    for gen in generators:
        if gen['name'].lower() == name.lower():
            return gen
    return None


# Calculate Heat Rate as a function of MW output
def calculate_heat_rate(generator, mw_range):
    # Get the coefficients
    a = generator['coefficients']['a']
    b = generator['coefficients']['b']
    c = generator['coefficients']['c']

    # Calculate heat rate in BTU/KWh
    heat_rate = a * mw_range**2 + b * mw_range + c  # Assuming coefficients give BTU/KWh

    return heat_rate

# Calculate BTU consumption as a function of MW output
def calculate_btu_consumption(generator, mw_range):
    # Get the heat rate from calculate_heat_rate
    heat_rate = calculate_heat_rate(generator, mw_range)

    # Total BTU consumption = Heat Rate (BTU/KWh) * Output (MW) * 1000 
    btu_consumption = heat_rate * mw_range * 1000

    return btu_consumption

# Calculate total cost as a function of MW output
def calculate_total_cost(generator, mw_range, fuel_cost_per_mmbtu):
    # Convert fuel cost to $/BTU
    fuel_cost_per_btu = fuel_cost_per_mmbtu / 1_000_000

    # Get the coefficients
    a = generator['coefficients']['a']
    b = generator['coefficients']['b']
    c = generator['coefficients']['c']

    # Calculate total cost in $
    total_cost = (a * mw_range**2 + b * mw_range + c) * fuel_cost_per_btu * 1000

    return total_cost

# Calculate marginal cost per MWh as a function of MW output
def calculate_marginal_cost(generator, mw_range, fuel_cost_per_mmbtu):
    # Convert fuel cost to $/BTU
    fuel_cost_per_btu = fuel_cost_per_mmbtu / 1_000_000

    # Get the coefficients
    a = generator['coefficients']['a']
    b = generator['coefficients']['b']
    c = generator['coefficients']['c']

    # Define the symbolic variable
    P = sp.symbols('P')

    # Define the cost function
    cost_function = (a * P**2 + b * P + c) * fuel_cost_per_btu * 1000

    # Calculate the derivative (marginal cost)
    marginal_cost_function = sp.diff(cost_function, P)

    # Evaluate the marginal cost function over the MW range
    marginal_cost_per_mw = [marginal_cost_function.subs(P, mw).evalf() for mw in mw_range]

    return np.array(marginal_cost_per_mw)

# Main function
def main():
    # Load generators from JSON file
    generators = load_generators('Diagrams_Scripts/generation_data.json')

    # List available generators
    print("Available Generators:")
    for gen in generators:
        print(f"- {gen['name']}")

    # Select generator by name
    selected_name = input("\nEnter the name of the generator you want to analyze: ")
    generator = find_generator(generators, selected_name)

    if generator is None:
        print(f"Generator '{selected_name}' not found.")
        return

    # Define MW output range from minimum to maximum capacity
    capacity_mw = generator['capacity_mw']
    min_mw = capacity_mw * 0.25  # Assume minimum output is 25% of capacity
    max_mw = capacity_mw
    mw_range = np.linspace(min_mw, max_mw, 100)

    # Ask user for fuel cost
    fuel_cost_per_mmbtu = float(input("Enter the fuel cost ($/MMBTU): "))

    # Calculate Heat Rate
    heat_rate = calculate_heat_rate(generator, mw_range)

    # Plot Heat Rate Curve (Heat Rate vs MW)
    plt.figure()
    plt.plot(mw_range, heat_rate)
    plt.xlabel('MW Output')
    plt.ylabel('Heat Rate (BTU/KWh)')
    plt.title(f'Heat Rate Curve for {generator["name"]}')
    plt.grid(True)
    plt.show()

    # Calculate BTU consumption
    btu_consumption = calculate_btu_consumption(generator, mw_range)

    # Plot BTU Consumption Curve (BTUs vs MW)
    plt.figure()
    plt.plot(mw_range, btu_consumption)
    plt.xlabel('MW Output')
    plt.ylabel('BTUs Consumed')
    plt.title(f'BTU Consumption Curve for {generator["name"]}')
    plt.grid(True)
    plt.show()

    # Calculate Total Cost
    total_cost = calculate_total_cost(generator, mw_range, fuel_cost_per_mmbtu)

    # Plot Cost Curve ($ vs MW)
    plt.figure()
    plt.plot(mw_range, total_cost)
    plt.xlabel('MW Output')
    plt.ylabel('Total Cost ($)')
    plt.title(f'Cost Curve for {generator["name"]}')
    plt.grid(True)
    plt.show()

    # Calculate Marginal Cost per MWh
    marginal_cost_per_mw = calculate_marginal_cost(generator, mw_range, fuel_cost_per_mmbtu)

    # Plot Marginal Cost Curve ($/MW vs MW)
    plt.figure()
    plt.plot(mw_range, marginal_cost_per_mw)
    plt.xlabel('MW Output')
    plt.ylabel('Marginal Cost ($/MW)')
    plt.title(f'Marginal Cost Curve for {generator["name"]}')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()