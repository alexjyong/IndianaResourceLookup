from flask import Flask, request, jsonify, render_template
import requests
import os
import geopandas as gpd
from shapely.geometry import Point
import json
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# Define users and their passwords
users = {
    "admin": generate_password_hash("yourpassword")
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
@app.route('/geocode', methods=['GET'])
@auth.login_required
def geocode():
    address = request.args.get('address')
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }
    headers = {
        "User-Agent": "YourAppName (your@email.com)"
    }

    # Get lat/lon from Nominatim
    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()

    if response.status_code == 200 and data:
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
            "error": "Address not found or invalid"
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
