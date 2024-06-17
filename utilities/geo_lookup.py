import requests
import pandas as pd
import json
import re
import os
from math import radians, cos, sin, asin, sqrt
from collections import defaultdict
import geopandas as gpd
from shapely.geometry import Point
import geopy.distance

# Function to geocode an address using OpenCage API
def geocode_address_opencage(address):
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
        return float(latitude), float(longitude)
    else:
        return None, None

# Function to geocode an address using the local Nominatim server
def geocode_address_nominatim(address):
    """Geocodes an address using the local Nominatim server."""
    base_url = "http://localhost:8080/search"
    params = {
        "q": address,
        "format": "json"
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200 and data:
        latitude = data[0]['lat']
        longitude = data[0]['lon']
        return float(latitude), float(longitude)
    else:
        return None, None

# Function to load township boundaries from GeoJSON file
def load_township_boundaries(geojson_file):
    """Load the township boundaries from a GeoJSON file."""
    return gpd.read_file(geojson_file)

# Function to determine the township for given coordinates
def get_township(latitude, longitude, township_gdf):
    """Determines the township for given coordinates using GeoDataFrame."""
    point = Point(longitude, latitude)
    for index, row in township_gdf.iterrows():
        if row['geometry'].contains(point):
            return row['tl_2021_18_cousub_namelsad']
    return None

# Function to get trustee information for a given address using geocoding and township data
def get_trustee_info(address, township_data_file, geojson_file, geocode_func):
    """Determines the township trustee using geocoding and township boundaries."""
    try:
        with open(township_data_file, 'r') as f:
            township_data = json.load(f)
        df_townships = pd.DataFrame(township_data)
    except FileNotFoundError:
        return "Township data file not found. Please check the file path."

    latitude, longitude = geocode_func(address)

    if latitude is None or longitude is None:
        return "Address not found or invalid."

    township_gdf = load_township_boundaries(geojson_file)
    township_name = get_township(latitude, longitude, township_gdf)

    if township_name:
        trustee_info = df_townships[df_townships['Name'].str.contains(township_name, case=False)]
        if not trustee_info.empty:
            trustee = trustee_info.iloc[0]
            return (f"Your trustee is: {trustee['Name']}\n"
                    f"Phone: {trustee['Phone']}\n"
                    f"Address: {trustee['Address']}\n")
        else:
            return f"Trustee information not found for {township_name} township."

    return "No trustee found for the provided address."

# Example usage:
address_to_search = "412 E 6th St, Bloomington, IN 47408"

# Using OpenCage API
# opencage_result = get_trustee_info(
#     address_to_search,
#     "data/indiana_township_trustees.json",
#     "data/indiana_townships.geojson",
#     geocode_address_opencage
# )

# Using local Nominatim server
nominatim_result = get_trustee_info(
    address_to_search,
    "data/indiana_township_trustees.json",
    "data/indiana_townships.geojson",
    geocode_address_nominatim
)

print(f"OpenCage API Result:\n{opencage_result}\n")
print(f"Nominatim Server Result:\n{nominatim_result}\n")
