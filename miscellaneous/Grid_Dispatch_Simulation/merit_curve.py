import numpy as np
import matplotlib.pyplot as plt

# Define the quadratic merit curve coefficients
a = 0.05       # Quadratic coefficient ($/MW²)
b = 50         # Linear coefficient ($/MW)
c_fixed = 10000  # Fixed cost ($)

# Define maximum capacity
x_max = 1000  # MW

# Define breakpoints for piecewise linear segments
# You can adjust these breakpoints based on desired accuracy
breakpoints = [0, 400, 700, x_max]  # MW

# Function to calculate the quadratic cost
def quadratic_cost(x):
    return a * x**2 + b * x + c_fixed

# Function to calculate linear approximation coefficients for a segment
def linear_approximation(x1, x2):
    # Calculate the slope (m) and intercept (c) of the line between two points
    y1 = quadratic_cost(x1)
    y2 = quadratic_cost(x2)
    m = (y2 - y1) / (x2 - x1)
    c = y1 - m * x1
    return m, c

# Calculate linear coefficients for each segment
linear_segments = []
for i in range(len(breakpoints) - 1):
    x1 = breakpoints[i]
    x2 = breakpoints[i + 1]
    m, c = linear_approximation(x1, x2)
    linear_segments.append({'segment': i+1, 'x_start': x1, 'x_end': x2, 'slope': m, 'intercept': c})

# Display the coefficients for each linear segment
print("Piecewise Linear Approximation Coefficients:")
print("==========================================")
for seg in linear_segments:
    print(f"Segment {seg['segment']}:")
    print(f"  Range: {seg['x_start']} MW ≤ x ≤ {seg['x_end']} MW")
    print(f"  Cost Function: C(x) = {seg['slope']:.4f}x + {seg['intercept']:.2f}")
    print("------------------------------------------")

# (Optional) Visualization of the quadratic curve and its piecewise linear approximation
x_vals = np.linspace(0, x_max, 500)
y_quadratic = quadratic_cost(x_vals)

# Calculate piecewise linear approximation
y_piecewise = np.piecewise(
    x_vals,
    [
        (x_vals >= breakpoints[0]) & (x_vals < breakpoints[1]),
        (x_vals >= breakpoints[1]) & (x_vals < breakpoints[2]),
        (x_vals >= breakpoints[2]) & (x_vals <= breakpoints[3]),
    ],
    [
        lambda x: linear_segments[0]['slope'] * x + linear_segments[0]['intercept'],
        lambda x: linear_segments[1]['slope'] * x + linear_segments[1]['intercept'],
        lambda x: linear_segments[2]['slope'] * x + linear_segments[2]['intercept'],
    ]
)

# Function to calculate the marginal cost (derivative of the quadratic cost function)
def marginal_cost(x):
    return 2 * a * x + b

# Calculate marginal cost values
y_marginal = marginal_cost(x_vals)

# Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot quadratic merit curve and piecewise linear approximation on primary y-axis
ax1.plot(x_vals, y_quadratic, label='Quadratic Merit Curve', color='blue')
ax1.plot(x_vals, y_piecewise, label='Piecewise Linear Approximation', color='red', linestyle='--')
ax1.scatter(breakpoints, [quadratic_cost(x) for x in breakpoints], color='green', zorder=5, label='Breakpoints')
ax1.set_xlabel('Capacity Utilization (MW)')
ax1.set_ylabel('Total Cost ($)')
ax1.legend(loc='upper left')
ax1.grid(True)

# Create secondary y-axis for marginal cost
ax2 = ax1.twinx()
ax2.plot(x_vals, y_marginal, label='Marginal Cost', color='purple')
ax2.set_ylabel('Marginal Cost ($/MW)')
ax2.legend(loc='upper right')

plt.title('Quadratic Merit Curve, Piecewise Linear Approximation, and Marginal Cost')
plt.show()
