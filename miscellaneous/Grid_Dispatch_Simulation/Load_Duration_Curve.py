import pandas as pd
import json
import matplotlib.pyplot as plt

# Define the input JSON file path
input_file = 'Diagrams_Scripts/Data_for_MoEnergy.json'

# Read the JSON file
with open(input_file, mode='r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Convert the JSON data to a pandas DataFrame
data = pd.DataFrame(data)

# Convert the MW column to numeric in case it's read as string
data['MW'] = pd.to_numeric(data['MW'], errors='coerce')

# Sort the data in descending order by the MW to create the load duration curve
sorted_data = data['MW'].sort_values(ascending=False).reset_index(drop=True)

# Generate a percentage of hours to plot the curve (x-axis)
percent_of_time = sorted_data.index / len(sorted_data) * 100

# Create the load duration curve plot
plt.figure(figsize=(10,6))
plt.plot(percent_of_time, sorted_data)
plt.title('Load Duration Curve')
plt.xlabel('Percentage of Time (%)')
plt.ylabel('Power Demand (MW)')
plt.grid(True)
plt.show()
