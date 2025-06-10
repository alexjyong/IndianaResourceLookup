from flask import Flask, request, jsonify, render_template
import requests
import os
import geopandas as gpd
from shapely.geometry import Point
import json
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

app = Flask(__name__)
auth = HTTPBasicAuth()

# Load environment variables from dotenv file

load_dotenv()
# Ensure the environment variable is set
if 'PASSWORD' not in os.environ:
    raise ValueError("Environment variable 'PASSWORD' not set. Please set it in your .env file.")

if 'USERNAME' not in os.environ:
    raise ValueError("Environment variable 'USERNAME' not set. Please set it in your .env file.")
# get username from os
username = os.getenv('USERNAME')
# get password from os
password = os.getenv('PASSWORD')

# Define users and their passwords
users = {
    username: generate_password_hash(password)
}

# Verify passwords
@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Load township boundaries
township_gdf = gpd.read_file('static/utilities/data/indiana_townships.geojson')

# Function to determine the township for given coordinates
def get_township(latitude, longitude):
    point = Point(longitude, latitude)
    for index, row in township_gdf.iterrows():
        if row['geometry'].contains(point):
            return row['cnty_name'], row['tl_2021_18_cousub_namelsad']
    return None, None

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/geocode', methods=['GET'])
@auth.login_required
def geocode():
    address = request.args.get('address')
    zip = request.args.get('zip')
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "format": "json",
        "addressdetails": 1
    }

    if zip:
        params['postalcode'] = zip
    if address:
        params['q'] = address
        params['limit'] = 1
    headers = {
        "User-Agent": "Indiana Resource Lookup"
    }


    # Get lat/lon from Nominatim
    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()
    print(data)
    if response.status_code == 200 and data:

        if zip:
            # if a zip code is provided, loop through each result and find the one with a state of Indiana
            for item in data:
                print (item)
                if 'state' in item['address'] and item['address']['state'].lower() == 'indiana':
                    location = item
                    break
            else:
                # if no location with Indiana state is found, return the first result
                location = data[0]
        else:
            # if we are using an address, just take the first result
            location = data[0]
        latitude = float(location['lat'])
        longitude = float(location['lon'])

        # Use the township lookup
        county, township = get_township(latitude, longitude)

        if county and township:
            return get_trustee_info(county, township)
        else:
            return jsonify({
                "latitude": latitude,
                "longitude": longitude,
                "message": "No township found for the provided coordinates"
            })
    else:
        return jsonify({
            "error": "Nothing found for the provided address or zip code"
        })

def get_trustee_info(county, township):
    """Gets trustee information for a given county and township."""
    try:
        with open('static/utilities/data/indiana_township_trustees.json', 'r') as f:
            trustee_data = json.load(f)
        for trustee in trustee_data:
            if trustee['County'].lower() == county.lower() and trustee['Name'].lower().startswith(township.lower()):
                return jsonify({
                    "county": county,
                    "township": township,
                    "trustee": trustee
                })
        return jsonify({
            "county": county,
            "message": "No immediate trustee found for the provided address"
        })
    except FileNotFoundError:
        return jsonify({
            "error": "Trustee data file not found. Please check the file path."
        })

@app.route('/reverse-geocode', methods=['GET'])
@auth.login_required
def reverse_geocode():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    try:
        latitude = float(lat)
        longitude = float(lon)

        # Get township and county
        county, township = get_township(latitude, longitude)

        if not county or not township:
            return jsonify({"error": "No township found for the provided coordinates"}), 404
        # Get trustee data
        trustee_info = None
        try:
            with open('static/utilities/data/indiana_township_trustees.json', 'r') as f:
                trustees = json.load(f)
                for trustee in trustees:
                    if trustee['County'].lower() == county.lower() and trustee['Name'].lower().startswith(township.lower()):
                        trustee_info = trustee
                        break
        except FileNotFoundError:
            print("Trustee data file not found.")

        # Get food pantry data
        food_pantries = []
        try:
            with open('static/utilities/data/indiana_food_pantries.json', 'r') as f:
                pantries = json.load(f)
                for pantry in pantries:
                    if pantry['County'].lower() == county.lower():
                        food_pantries.append(pantry)
        except FileNotFoundError:
            print("Food pantry data file not found.")

        return jsonify({
            "trustee": trustee_info,
            "food_pantries": food_pantries
        })

    except ValueError:
        return jsonify({"error": "Invalid latitude or longitude"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
