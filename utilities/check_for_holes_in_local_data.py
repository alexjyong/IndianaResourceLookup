#finds what counties and townships are missing data in our trustee file
import json
import os
from collections import defaultdict

# Load data
def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

geojson_data = load_json('../static/utilities/data/indiana_townships.geojson')
trustee_data = load_json('../static/utilities/data/indiana_township_trustees.json')

# Cross-referencing and logging missing data
missing_offices = []
plain_text_missing_offices = []

missing_townships_count = 0
missing_counties = defaultdict(list)

for feature in geojson_data['features']:
    township_name = feature['properties']['tl_2021_18_cousub_namelsad'].replace(' Township', '')
    county_name = feature['properties']['cnty_name']

    # Check if the township exists in the trustee data
    if not any(trustee['Name'].lower().startswith(township_name.lower()) and trustee['County'].lower() == county_name.lower() for trustee in trustee_data):
        if township_name == "County Subdivisions Not Defined":
            continue

        missing_office = {
            "County": county_name,
            "Name": f"{township_name} Township Trustee",
            "Address": "",
            "Phone": "",
            "Website": "",
            "Latitude": "",
            "Longitude": "",
            "Hours": []
        }
        missing_offices.append(missing_office)
        plain_text_missing_offices.append(f"County: {county_name}, Township: {township_name}")
        missing_townships_count += 1
        missing_counties[county_name].append(township_name)

# Save missing offices to JSON
with open('missing_offices.json', 'w', encoding='utf-8') as json_file:
    json.dump(missing_offices, json_file, ensure_ascii=False, indent=4)

# Save missing offices to plaintext file
with open('missing_offices.txt', 'w', encoding='utf-8') as text_file:
    for line in plain_text_missing_offices:
        text_file.write(line + '\n')

# Print summary information
print(f"Total missing townships: {missing_townships_count}")
print(f"Total affected counties: {len(missing_counties)}")
print("Affected counties and their missing townships:")

for county, townships in missing_counties.items():
    print(f"{county}: {', '.join(townships)}")

print("Missing offices have been logged.")
