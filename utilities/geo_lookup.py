import requests
import pandas as pd
import json
import geopandas as gpd
import re
import os
from math import radians, cos, sin, asin, sqrt
from collections import defaultdict
import geopy.distance

# Function to load and group addresses
def load_addresses(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

def group_by_street(addresses):
    grouped = defaultdict(list)
    for addr in addresses:
        if addr.get('street'):
            grouped[addr['street'].lower()].append(addr)
    return grouped

def find_best_match(address, street_data):
    housenumber = int(re.search(r'\d+', address['housenumber']).group())
    candidates = []
    for addr in street_data:
        if addr['housenumber']:
            try:
                num = int(re.search(r'\d+', addr['housenumber']).group())
                candidates.append((addr, num))
            except ValueError:
                continue

    if not candidates:
        return None

    candidates.sort(key=lambda x: abs(x[1] - housenumber))
    best_match = candidates[0][0]
    
    return best_match

def interpolate_coordinates(address, street_data):
    best_match = find_best_match(address, street_data)
    if not best_match:
        return None, None

    housenumber = int(re.search(r'\d+', address['housenumber']).group())
    match_housenumber = int(re.search(r'\d+', best_match['housenumber']).group())
    
    if housenumber == match_housenumber:
        return best_match['latitude'], best_match['longitude']

    # Find nearest points for interpolation
    sorted_addresses = sorted(street_data, key=lambda x: int(re.search(r'\d+', x['housenumber']).group()))
    prev_point = None
    next_point = None

    for addr in sorted_addresses:
        num = int(re.search(r'\d+', addr['housenumber']).group())
        if num <= housenumber:
            prev_point = addr
        if num >= housenumber and next_point is None:
            next_point = addr

    if not prev_point or not next_point or prev_point == next_point:
        return best_match['latitude'], best_match['longitude']

    # Interpolation
    prev_coords = (prev_point['latitude'], prev_point['longitude'])
    next_coords = (next_point['latitude'], next_point['longitude'])
    
    total_distance = geopy.distance.distance(prev_coords, next_coords).meters
    distance_to_prev = geopy.distance.distance(prev_coords, (best_match['latitude'], best_match['longitude'])).meters
    fraction = distance_to_prev / total_distance

    interpolated_lat = prev_coords[0] + fraction * (next_coords[0] - prev_coords[0])
    interpolated_lon = prev_coords[1] + fraction * (next_coords[1] - prev_coords[1])

    return interpolated_lat, interpolated_lon

def geocode_address(address):
    """Geocodes an address using the OpenCage Geocoding API."""
    api_key = os.getenv("OPENCAGEDATA")
    base_url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": address,
        "key": api_key
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200 and data['results']:
        latitude = data['results'][0]['geometry']['lat']
        longitude = data['results'][0]['geometry']['lng']
        state = data['results'][0]['components'].get('state_code')  
        return latitude, longitude, state
    else:
        return None, None, None

def load_tiger_shapefile(shapefile_path):
    """Load the TIGER/Line shapefile."""
    return gpd.read_file(shapefile_path)

def estimate_coordinates_from_address_range(address, tiger_df):
    """Estimate coordinates for an address using TIGER/Line address ranges."""
    match = re.search(r"(\d+)\s+(.*),\s*([\w\s]+),\s*(\w{2})\s*(\d{5})?", address)
    if not match:
        return None, None, None

    housenumber = int(match.group(1))
    street = match.group(2).lower()
    city = match.group(3)
    state = match.group(4)
    zipcode = match.group(5)

    # Filter TIGER/Line data for the relevant street
    street_data = tiger_df[tiger_df['FULLNAME'].str.lower().str.contains(street)]
    
    if street_data.empty:
        return None, None, None

    # Using the first match for simplicity
    row = street_data.iloc[0]
    line = row['geometry']
    point = line.interpolate(0.5, normalized=True)  # Approximate midpoint of the line
    return point.y, point.x, state

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth."""
    R = 6371  # Radius of earth in kilometers. Use 3956 for miles
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    return R * c

def get_township_from_geojson(latitude, longitude, geojson_file):
    """Determines the township from a GeoJSON file."""
    try:
        townships = gpd.read_file(geojson_file) 
        point = gpd.points_from_xy([longitude], [latitude], crs=townships.crs)[0]

        for index, row in townships.iterrows():
            if row['geometry'].contains(point):
                return row['tl_2021_18_cousub_namelsad']
    except FileNotFoundError:
        return None
    return None

def get_trustee_info_geojson(address, township_data_file, geojson_file, osm_addresses_file):
    """Determines the township trustee using local GeoJSON data and OSM addresses."""
    try:
        with open(township_data_file, 'r') as f:
            township_data = json.load(f)
        df_townships = pd.DataFrame(township_data)
    except FileNotFoundError:
        return "Township data file not found. Please check the file path."

    # Parse address (using regular expressions)
    match = re.search(r"(.*),\s*([\w\s]+),\s*(\w{2})\s*(\d{5})?", address)
    if match:
        street = match.group(1)
        city = match.group(2)
        state = match.group(3)
        zipcode = match.group(4)
    else:
        return "Invalid address format. Please use 'Street, City, State Zipcode'."

    # State Check
    if state.upper() != 'IN':
        return "Address is outside of Indiana. This service only covers Indiana townships."

    # Load OSM addresses and group by street
    addresses = load_addresses(osm_addresses_file)
    grouped_addresses = group_by_street(addresses)
    
    address_to_geocode = {
        'housenumber': match.group(1),
        'street': street,
        'city': city,
        'state': state,
        'postcode': zipcode
    }

    street_data = grouped_addresses.get(address_to_geocode['street'].lower())
    if not street_data:
        return "Address not found in OSM data."

    # Interpolate coordinates from OSM addresses
    latitude, longitude = interpolate_coordinates(address_to_geocode, street_data)
    if latitude is None or longitude is None:
        return "Address not found or invalid."

    # Get Township from GeoJSON
    township_name = get_township_from_geojson(latitude, longitude, geojson_file)

    if township_name:
        trustee_info = df_townships[df_townships['Name'].str.contains(township_name, case=False)]
        if not trustee_info.empty:
            trustee = trustee_info.iloc[0]
            return (f"Your trustee is: {trustee['Name']}\n"
                    f"Phone: {trustee['Phone']}\n"
                    f"Address: {trustee['Address']}\n")
        else:
            return f"Trustee information not found for {township_name} township."

    return "No trustee found using GeoJSON data."

def get_trustee_info_api(address, township_data_file, max_distance_threshold=50):
    """Determines the township trustee using the API and distance calculation."""
    try:
        with open(township_data_file, 'r') as f:
            township_data = json.load(f)
        df_townships = pd.DataFrame(township_data)
    except FileNotFoundError:
        return "Township data file not found. Please check the file path."

    latitude, longitude, state = geocode_address(address)

    if latitude is None or longitude is None:
        return "Address not found or invalid."

    # State Check (Important for distance-based method!)
    if state and state.upper() != 'IN':
        return "Address is outside of Indiana. This service only covers Indiana townships."

    df_townships['distance'] = df_townships.apply(
        lambda row: haversine_distance(latitude, longitude, row['Latitude'], row['Longitude']),
        axis=1
    )
    nearest_township = df_townships.loc[df_townships['distance'].idxmin()]
    min_distance = nearest_township['distance']

    if min_distance <= max_distance_threshold:
        trustee = nearest_township
        return (f"Your trustee is: {trustee['Name']}\n"
                f"Phone: {trustee['Phone']}\n"
                f"Address: {trustee['Address']}\n")

    return "No trustee found within a reasonable distance using API data."

# Example usage:
address_to_search = "325 E Winslow Rd, Bloomington, IN 47401"

api_result = get_trustee_info_api(
    address_to_search,
    "data/indiana_township_trustees.json"
)

geojson_result = get_trustee_info_geojson(
    address_to_search, 
    "data/indiana_township_trustees.json", 
    "data/indiana_townships.geojson", 
    "data/indiana_addresses.json"  # Processed OSM address data
)

print(f"GeoJSON Result:\n{geojson_result}\n")
print(f"API Result:\n{api_result}\n")
