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

# Convert the Hour column to numeric (integer) in case it's read as string
data['Hour'] = pd.to_numeric(data['Hour'], errors='coerce')

# Convert the Hour column to datetime format assuming it represents hours in a year
data['Hour'] = pd.to_datetime(data['Hour'], unit='h', origin=pd.Timestamp('2023-01-01'))

# Set the Hour column as the index
data.set_index('Hour', inplace=True)

print(data)

# Resample the data to daily frequency and calculate the daily sum
daily_data = data.resample('D').sum()

# Print the daily data
print(daily_data)

# Find the most demanding and least demanding days
most_demanding_day = daily_data['MW'].idxmax()
least_demanding_day = daily_data['MW'].idxmin()

# Print the data for the least demanding day
print(f"Data for the least demanding day ({least_demanding_day.date()}):")
print(data.loc[least_demanding_day.strftime('%Y-%m-%d')])

print(most_demanding_day)
print(least_demanding_day)

# Create subplots
fig, axs = plt.subplots(3, 1, figsize=(12, 18))

# Display the load profile for the full year
axs[0].plot(data.index, data['MW'], label='Hourly Load')
axs[0].set_title('Load Profile for the Full Year')
axs[0].set_xlabel('Time')
axs[0].set_ylabel('Power Demand (MW)')
axs[0].legend()
axs[0].grid(True)

# Zoom in on the most demanding day
axs[1].plot(data.loc[most_demanding_day.strftime('%Y-%m-%d')].index, data.loc[most_demanding_day.strftime('%Y-%m-%d')]['MW'], label='Most Demanding Day', color='r')
axs[1].set_title('Zoomed In: Most Demanding Day')
axs[1].set_xlabel('Time')
axs[1].set_ylabel('Power Demand (MW)')
axs[1].legend()
axs[1].grid(True)

# Zoom in on the least demanding day
axs[2].plot(data.loc[least_demanding_day.strftime('%Y-%m-%d')].index, data.loc[least_demanding_day.strftime('%Y-%m-%d')]['MW'], label='Least Demanding Day', color='g')
axs[2].set_title('Zoomed In: Least Demanding Day')
axs[2].set_xlabel('Time')
axs[2].set_ylabel('Power Demand (MW)')
axs[2].legend()
axs[2].grid(True)

# Adjust layout
plt.tight_layout()
plt.show()

# Display the most demanding and least demanding days
print(f"Most Demanding Day: {most_demanding_day.date()} with {daily_data['MW'].max()} MW")
print(f"Least Demanding Day: {least_demanding_day.date()} with {daily_data['MW'].min()} MW")
