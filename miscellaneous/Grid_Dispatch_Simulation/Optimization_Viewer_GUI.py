import json
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd  # Add pandas for table display
import random  # Add import for random
from matplotlib.animation import FuncAnimation
from scipy.interpolate import make_interp_spline
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

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
def animate_load_profile(load_profile, dispatches, reserves):
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2)
    
    ax1 = fig.add_subplot(gs[0, :])  # Full year plot
    ax2 = fig.add_subplot(gs[1, 0])  # 25-hour window plot
    ax3 = fig.add_subplot(gs[1, 1])  # Generator dispatch and reserves bar plot

    hours = np.arange(len(load_profile))
    window_size = 25  # 12 hours before + current hour + 12 hours after

    # Smooth the load profile for the full year plot
    smooth_hours = np.linspace(0, len(load_profile) - 1, len(load_profile) * 10)
    smooth_load = make_interp_spline(hours, load_profile)(smooth_hours)

    # Full year plot
    line_full, = ax1.plot(smooth_hours, smooth_load, lw=1, color='#1f77b4')
    ax1.set_xlim(0, len(load_profile) - 1)
    ax1.set_ylim(min(load_profile) * 0.9, max(load_profile) * 1.1)
    ax1.set_title('Full Year Load Profile', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Hours of the Year', fontsize=10)
    ax1.set_ylabel('Load (MW)', fontsize=10)
    vertical_line = ax1.axvline(x=0, color='r', linestyle='--')

    # 25-hour window plot
    line_window, = ax2.plot([], [], lw=2, color='#1f77b4')
    ax2.set_xlim(0, window_size - 1)
    ax2.set_ylim(min(load_profile) * 0.8, max(load_profile) * 1.2)  # Increased y-axis range
    ax2.set_title('25-Hour Window', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Hours', fontsize=10)
    ax2.set_ylabel('Load (MW)', fontsize=10)

    # Generator dispatch and reserves bar plot
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

    x = np.arange(len(gen_order))
    dispatch_bars = ax3.bar(x, [0] * len(gen_order), color=[colors[gen] for gen in gen_order], label='Dispatch')
    reserve_bars = ax3.bar(x, [0] * len(gen_order), bottom=[0] * len(gen_order), 
                           color=[colors[gen] for gen in gen_order], alpha=0.5, label='Reserves')
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(gen_order, rotation=45, ha='right')
    ax3.set_title('Generator Dispatch and Reserves', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Generator Types', fontsize=10)
    ax3.set_ylabel('Power (MW)', fontsize=10)
    ax3.legend()
    
    # Set the y-axis limit for the bar plot to the maximum total value (dispatch + reserves)
    max_total = max(max(dispatches[gen_type]) + max(reserves[gen_type]) for gen_type in gen_order)
    ax3.set_ylim(0, max_total * 1.1)

    def init():
        line_window.set_data([], [])
        for bar in dispatch_bars:
            bar.set_height(0)
        for bar in reserve_bars:
            bar.set_height(0)
            bar.set_y(0)
        return [line_window] + list(dispatch_bars) + list(reserve_bars) + [vertical_line]

    def update(frame):
        # Update full year plot
        vertical_line.set_xdata(frame)

        # Update 25-hour window plot
        start = max(0, frame - 12)
        end = min(len(load_profile), frame + 13)
        x = hours[start:end] - start
        y = load_profile[start:end]
        line_window.set_data(x, y)
        
        # Update y-axis limits for the 25-hour window plot every 100 frames
        if frame % 10 == 0:
            ax2.set_ylim(min(y) * 0.8, max(y) * 1.2)  # Increased y-axis range
        
        ax2.set_title(f'25-Hour Window', fontsize=12, fontweight='bold')

        # Update generator dispatch and reserves bar plot
        for i, gen_type in enumerate(gen_order):
            dispatch_height = dispatches[gen_type][frame]
            reserve_height = reserves[gen_type][frame]
            dispatch_bars[i].set_height(dispatch_height)
            reserve_bars[i].set_height(reserve_height)
            reserve_bars[i].set_y(dispatch_height)
        ax3.set_title(f'Generator Dispatch and Reserves', fontsize=12, fontweight='bold')

        return [line_window] + list(dispatch_bars) + list(reserve_bars) + [vertical_line]

    ani = FuncAnimation(fig, update, frames=len(load_profile),
                        init_func=init, blit=True, interval=25)
    plt.tight_layout()
    plt.show()

# Main function to handle user interaction
def main():
    def load_file():
        filepath = filedialog.askopenfilename(
            initialdir='./Simulation_Results',
            title="Select JSON file",
            filetypes=(("JSON files", "*.json"), ("all files", "*.*"))
        )
        if not filepath:
            return
        data = load_results_from_json(filepath)
        results = data["results"]
        timing_filepath = './Diagrams_Scripts/BSC_Saudi_Timing.json'
        timing_definitions = load_timing_definitions(timing_filepath)
        enable_buttons(results, timing_definitions)

    def plot_choice(choice, results, timing_definitions):
        for widget in right_frame.winfo_children():
            widget.destroy()
        
        if choice == '1':
            plot_merit_curve_and_marginal_cost(results["load_profile"], results["total_costs"], results["marginal_costs"])
        elif choice == '2':
            plot_total_marginal_and_average_cost_vs_hours(results["load_profile"], results["total_costs"], results["marginal_costs"])
        elif choice == '3':
            plot_total_and_average_cost_vs_hours(results["load_profile"], results["total_costs"])
        elif choice == '4':
            plot_dispatch_for_load_profile(results["load_profile"], results["dispatches"])
        elif choice == '5':
            plot_daily_total_and_average_cost(results["load_profile"], results["total_costs"])
        elif choice == '6':
            plot_wind_and_solar_dispatch(results["load_profile"], results["dispatches"])
        elif choice == '7':
            average_prices_all_months = calculate_average_prices_for_all_months(results["load_profile"], results["total_costs"], timing_definitions)
            df = pd.DataFrame(average_prices_all_months).T
            text = tk.Text(right_frame)
            text.insert(tk.END, df.to_string())
            text.pack(expand=True, fill='both')
        elif choice == '8':
            weekly_max_load = calculate_weekly_max_load(results["load_profile"])
            plot_weekly_max_load(weekly_max_load)
        elif choice == '9':
            scale_dispatches_gui(results)
        elif choice == '10':
            if "reserves" in results:
                animate_load_profile(results["load_profile"], results["dispatches"], results["reserves"])
            else:
                messagebox.showerror("Error", "Reserves data not available in the JSON file.")
        else:
            messagebox.showerror("Error", "Invalid choice.")

    def scale_dispatches_gui(results):
        def scale_dispatches():
            scaling_choice = scaling_var.get()
            if scaling_choice == '1':
                scaling_factor = float(scaling_factor_entry.get())
                scaled_dispatches = scale_dispatches_uniformly(results["dispatches"], scaling_factor)
            elif scaling_choice == '2':
                min_percentage = float(min_percentage_entry.get())
                max_percentage = float(max_percentage_entry.get())
                scaled_dispatches = scale_dispatches_randomly(results["dispatches"], min_percentage, max_percentage)
            else:
                messagebox.showerror("Error", "Invalid choice.")
                return

            results["dispatches"] = scaled_dispatches
            directory, filename = os.path.split(filepath)
            save_json(data, filename)
            scale_window.destroy()

        scale_window = tk.Toplevel(root)
        scale_window.title("Scale Dispatches")

        scaling_var = tk.StringVar(value='1')
        tk.Radiobutton(scale_window, text="Uniform scaling", variable=scaling_var, value='1').pack(anchor='w')
        tk.Radiobutton(scale_window, text="Random scaling", variable=scaling_var, value='2').pack(anchor='w')

        tk.Label(scale_window, text="Scaling factor:").pack(anchor='w')
        scaling_factor_entry = tk.Entry(scale_window)
        scaling_factor_entry.pack(anchor='w')

        tk.Label(scale_window, text="Min percentage:").pack(anchor='w')
        min_percentage_entry = tk.Entry(scale_window)
        min_percentage_entry.pack(anchor='w')

        tk.Label(scale_window, text="Max percentage:").pack(anchor='w')
        max_percentage_entry = tk.Entry(scale_window)
        max_percentage_entry.pack(anchor='w')

        tk.Button(scale_window, text="Scale", command=scale_dispatches).pack()

    def enable_buttons(results, timing_definitions):
        for i, option in enumerate(options):
            button = ttk.Button(left_frame, text=option, command=lambda opt=i+1: plot_choice(str(opt), results, timing_definitions))
            button.pack(fill='x', pady=5)

    root = tk.Tk()
    root.title("Optimization Viewer")
    root.state('zoomed')  # Maximize the window

    # Create a main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True)

    # Create left and right frames
    left_frame = ttk.Frame(main_frame, width=200)
    left_frame.pack(side='left', fill='y')
    right_frame = ttk.Frame(main_frame)
    right_frame.pack(side='right', fill='both', expand=True)

    tk.Button(left_frame, text="Load JSON File", command=load_file).pack(fill='x', pady=5)

    options = [
        "1. Merit Curve and Marginal Cost",
        "2. Total Cost, Marginal Cost, and Average Cost vs Hour of the Year",
        "3. Total Cost and Average Cost vs Hour of the Year (without Marginal Cost)",
        "4. Dispatch per Type of Generation vs Hour of the Year (Stacked Area)",
        "5. Daily Total Cost and Average Cost vs Day of the Year (Daily Averages)",
        "6. Wind and Solar Dispatch vs Hour of the Year (Stacked Area)",
        "7. Calculate average $/MWh price for each group in a month",
        "8. Plot weekly maximum load",
        "9. Scale dispatches",
        "10. Animate Load Profile"
    ]

    root.mainloop()

if __name__ == "__main__":
    main()