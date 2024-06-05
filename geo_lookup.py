import requests
import pandas as pd
import json
import geopandas as gpd
import re
from math import radians, cos, sin, asin, sqrt

def geocode_address(address):
    """Geocodes an address using the OpenCage Geocoding API.

    Args:
        address (str): The address to geocode.

    Returns:
        tuple: Latitude, longitude coordinates, and state 
               or (None, None, None) if geocoding fails.
    """
    api_key = "" 
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

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using the Haversine formula.
    Returns distance in kilometers.
    """
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

def get_trustee_info_geojson(address, township_data_file, geojson_file):
    """Determines the township trustee using local GeoJSON data ONLY.
       No API calls are made."""

    try:
        with open(township_data_file, 'r') as f:
            township_data = json.load(f)
        df_townships = pd.DataFrame(township_data)
    except FileNotFoundError:
        return "Township data file not found. Please check the file path."

    # --- Address Parsing (using regular expressions) ---
    match = re.search(r"(.*),\s*([\w\s]+),\s*(\w{2})\s*(\d{5})?", address)
    if match:
        street = match.group(1)
        city = match.group(2)
        state = match.group(3)
        zipcode = match.group(4)
    else:
        return "Invalid address format. Please use 'Street, City, State Zipcode'."

    # --- State Check --- 
    if state.upper() != 'IN':
        return "Address is outside of Indiana. This service only covers Indiana townships."

    # --- Get Latitude and Longitude from User Input (You'll need to implement this!) ---
    latitude, longitude = get_coordinates_from_input(address)

    # --- Get Township from GeoJSON ---
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

def get_coordinates_from_input(address):
    """
    Prompts the user to enter latitude and longitude for the given address. 

    Args:
        address (str): The full address string.

    Returns:
        tuple: (latitude, longitude) as floats, or (None, None) if input is invalid.
    """
    print(f"Please enter the latitude and longitude for the following address:\n{address}")
    while True:
        try:
            latitude = float(input("Latitude: "))
            longitude = float(input("Longitude: "))
            return latitude, longitude
        except ValueError:
            print("Invalid input. Please enter numeric values for latitude and longitude.")

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



# geojson_result = get_trustee_info_geojson(
#     address_to_search, 
#     "indiana_township_trustees.json", 
#     "localgeodata/indiana_townships.geojson" 
# )
# print(f"GeoJSON Result:\n{geojson_result}\n")

api_result = get_trustee_info_api(
    address_to_search,
    "indiana_township_trustees.json"
)
print(f"API Result:\n{api_result}\n")