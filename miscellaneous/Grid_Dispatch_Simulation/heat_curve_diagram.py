import json
import numpy as np
import matplotlib.pyplot as plt

# JSON data as before
json_data = '''
[
  {
    "name": "Gas Turbine",
    "coefficients": {"a": 12.22, "b": -11166.7, "c": 11527780},
    "fuel_cost_per_btu": 0.000003
  },
  {
    "name": "Crude Oil Fired",
    "coefficients": {"a": 12.22, "b": -11166.7, "c": 11527780},
    "fuel_cost_per_btu": 0.000003
  },
  {
    "name": "Combined Cycle Gas Turbine",
    "coefficients": {"a": 12.22, "b": -11166.7, "c": 11527780},
    "fuel_cost_per_btu": 0.000003
  },
  {
    "name": "Photovoltaic Solar",
    "coefficients": null,
    "fuel_cost_per_btu": 0
  },
  {
    "name": "Wind Turbine",
    "coefficients": null,
    "fuel_cost_per_btu": 0
  },
  {
    "name": "Simple Cycle Gas Turbine",
    "coefficients": {"a": 12.22, "b": -11166.7, "c": 11527780},
    "fuel_cost_per_btu": 0.000003
  }
]
'''

# Load JSON data
generators = json.loads(json_data)

# Power output range (in MW)
P = np.linspace(50, 500, 100)

# Initialize plot
fig, ax1 = plt.subplots(figsize=(12, 8))

# Define colors for consistency
colors = plt.cm.tab10.colors  # Use built-in colormap

# Create secondary y-axis outside the loop
ax2 = ax1.twinx()

for idx, gen in enumerate(generators):
    name = gen['name']
    coeffs = gen['coefficients']
    fuel_cost_per_btu = gen['fuel_cost_per_btu']
    
    if coeffs is not None and fuel_cost_per_btu > 0:
        a = coeffs['a']
        b = coeffs['b']
        c = coeffs['c']
        
        # Calculate Heat Input H(P) in BTU/hr
        H = a * P**2 + b * P + c  # BTU/hr
        
        # Calculate Heat Rate in BTU per kWh
        energy_output_kwh = P * 1000  # kW (since energy over one hour, kWh)
        heat_rate_btu_per_kwh = H / energy_output_kwh  # BTU/kWh
        
        # Calculate Running Cost C(P) in $
        C = H * fuel_cost_per_btu  # $
        
        # Calculate Cost per MWh
        cost_per_mwh = C / P  # $/MWh
        
        # Plot Cost per MWh on primary y-axis
        ax1.plot(P, cost_per_mwh, label=f"{name} Cost", color=colors[idx % len(colors)], linestyle='-')
        
        # Plot Heat Rate on secondary y-axis
        ax2.plot(P, heat_rate_btu_per_kwh, label=f"{name} Heat Rate", color=colors[idx % len(colors)], linestyle='--')
        
    else:
        # For generators without fuel costs (e.g., Solar, Wind)
        # Set cost and heat rate to zero for plotting purposes
        cost_per_mwh = np.zeros_like(P)
        heat_rate_btu_per_kwh = np.zeros_like(P)
        
        # Plot Cost per MWh on primary y-axis
        ax1.plot(P, cost_per_mwh, label=f"{name} Cost", color=colors[idx % len(colors)], linestyle='-')
        
        # Plot Heat Rate on secondary y-axis (will be zero)
        ax2.plot(P, heat_rate_btu_per_kwh, label=f"{name} Heat Rate", color=colors[idx % len(colors)], linestyle='--')

# Customize primary y-axis (Cost per MWh)
ax1.set_xlabel('Power Output (MW)')
ax1.set_ylabel('Cost per MWh ($/MWh)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# Customize secondary y-axis (Heat Rate)
ax2.set_ylabel('Heat Rate (BTU/kWh)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Combine legends from both axes
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2)

# Add grid
ax1.grid(True)

# Set plot title
plt.title('Cost and Heat Rate Curves for Different Generators')

# Show plot
plt.tight_layout()
plt.show()
