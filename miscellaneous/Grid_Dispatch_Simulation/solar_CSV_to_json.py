import csv
import json
import os

# Define file paths
csv_file_path = './Diagrams_Scripts/Solar_Profile.csv'
json_file_path = './Diagrams_Scripts/Solar_Profile.json'

# Read the CSV file with utf-8-sig encoding to handle BOM
data = []
with open(csv_file_path, mode='r', encoding='utf-8-sig') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        data.append(row)

# Write the JSON file
with open(json_file_path, mode='w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"CSV data has been converted to JSON and saved to {json_file_path}")
