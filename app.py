from flask import Flask, request, jsonify, render_template
import requests
import geopandas as gpd
from shapely.geometry import Point
import json
import config
import time
import threading
import logging
from logging.handlers import RotatingFileHandler
from cachetools import TTLCache

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
log_handler = RotatingFileHandler('app.log', maxBytes=10_000_000, backupCount=5)
log_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)


@app.after_request
def add_security_headers(response):
    # Restrict third-party resources to the minimum needed for map and UI functionality.
    csp = (
        "default-src 'self'; "
        "script-src 'self' https://code.jquery.com https://unpkg.com; "
        "style-src 'self' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src-elem 'self' https://cdn.jsdelivr.net https://unpkg.com; "
        "img-src 'self' data: https://tile.openstreetmap.org https://*.tile.openstreetmap.org https://*.openstreetmap.org https://raw.githubusercontent.com https://cdnjs.cloudflare.com; "
        "connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org https://*.openstreetmap.org; "
        "font-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self' https://formspree.io"
    )
    response.headers['Content-Security-Policy'] = csp
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Permissions-Policy'] = 'geolocation=(self), camera=(), microphone=()'
    return response


@app.before_request
def log_request():
    app.logger.info('%s %s from %s', request.method, request.path, request.remote_addr)


class RateLimiter:
    def __init__(self, min_interval=1.0):
        self.min_interval = min_interval
        self.last_request_time = 0
        self.lock = threading.Lock()

    def wait_if_needed(self):
        with self.lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time

            if time_since_last_request < self.min_interval:
                sleep_time = self.min_interval - time_since_last_request
                time.sleep(sleep_time)

            self.last_request_time = time.time()

nominatim_limiter = RateLimiter(min_interval=1.0)

geocode_cache = TTLCache(maxsize=500, ttl=3600)

def get_cached_geocode(query):
    return geocode_cache.get(query)

def cache_geocode(query, result):
    geocode_cache[query] = result

township_gdf = gpd.read_file(config.TOWNSHIP_GEO_FILE)
app.logger.info('Township GeoJSON loaded (%d features)', len(township_gdf))

try:
    with open(config.TRUSTEE_DATA_FILE, 'r') as f:
        trustee_data_cache = json.load(f)
    app.logger.info('Trustee data loaded (%d records)', len(trustee_data_cache))
except (FileNotFoundError, json.JSONDecodeError) as e:
    app.logger.error('Failed to load trustee data: %s', e)
    raise

try:
    with open(config.FOOD_PANTRY_FILE, 'r') as f:
        food_pantry_data_cache = json.load(f)
    app.logger.info('Food pantry data loaded (%d records)', len(food_pantry_data_cache))
except (FileNotFoundError, json.JSONDecodeError) as e:
    app.logger.error('Failed to load food pantry data: %s', e)
    raise

def get_township(latitude, longitude):
    point = Point(longitude, latitude)
    possible_matches_index = list(township_gdf.sindex.intersection(point.bounds))
    possible_matches = township_gdf.iloc[possible_matches_index]

    for idx, row in possible_matches.iterrows():
        if row['geometry'].contains(point):
            return row['cnty_name'], row['tl_2021_18_cousub_namelsad']

    return None, None

def find_trustee_by_location(county, township):
    for trustee in trustee_data_cache:
        if trustee['County'].lower() == county.lower() and trustee['Name'].lower().startswith(township.lower()):
            return trustee
    return None

def find_food_pantries_by_county(county):
    return [pantry for pantry in food_pantry_data_cache if pantry['County'].lower() == county.lower()]

def validate_coordinates(latitude, longitude):
    try:
        lat = float(latitude)
        lon = float(longitude)

        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
        if not (-180 <= lon <= 180):
            return False, "Longitude must be between -180 and 180"

        if not (config.INDIANA_LAT_MIN <= lat <= config.INDIANA_LAT_MAX):
            return False, "Location is outside Indiana's latitude range"
        if not (config.INDIANA_LON_MIN <= lon <= config.INDIANA_LON_MAX):
            return False, "Location is outside Indiana's longitude range"

        return True, (lat, lon)
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/geocode', methods=['GET'])
def geocode():
    address = request.args.get('address')
    zip_code = request.args.get('zip')

    if not address and not zip_code:
        return jsonify({"error": "Address or zip code is required"}), 400

    cache_key = f"zip:{zip_code}" if zip_code else f"addr:{address}"
    cached_result = get_cached_geocode(cache_key)
    if cached_result:
        return cached_result

    params = {
        "format": "json",
        "addressdetails": 1
    }

    if zip_code:
        params['postalcode'] = zip_code
    if address:
        params['q'] = address
        params['limit'] = 1
    headers = {
        "User-Agent": config.NOMINATIM_USER_AGENT
    }

    try:
        nominatim_limiter.wait_if_needed()

        response = requests.get(config.NOMINATIM_BASE_URL, params=params, headers=headers, timeout=config.NOMINATIM_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if not data:
            return jsonify({"error": "No results found for the provided address or zip code"}), 404

        location = None
        if zip_code:
            for item in data:
                if 'state' in item.get('address', {}) and item['address']['state'].lower() == 'indiana':
                    location = item
                    break
            if not location:
                return jsonify({"error": "Zip code not found in Indiana"}), 404
        else:
            location = data[0]

        latitude = float(location['lat'])
        longitude = float(location['lon'])

        county, township = get_township(latitude, longitude)

        if county and township:
            result = get_trustee_info(county, township)
            cache_geocode(cache_key, result)
            return result
        else:
            return jsonify({
                "error": "Location is outside Indiana or township data unavailable"
            }), 404

    except requests.exceptions.Timeout:
        app.logger.warning('Nominatim request timed out for %s', cache_key)
        return jsonify({"error": "Request timed out. Please try again"}), 504
    except requests.exceptions.RequestException as e:
        app.logger.error('Nominatim connection error for %s: %s', cache_key, e)
        return jsonify({"error": f"Error connecting to geocoding service: {str(e)}"}), 503
    except (ValueError, KeyError) as e:
        app.logger.error('Invalid Nominatim response for %s: %s', cache_key, e)
        return jsonify({"error": "Invalid response from geocoding service"}), 500
    except Exception as e:
        app.logger.exception('Unexpected error in geocode for %s', cache_key)
        return jsonify({"error": "An unexpected error occurred"}), 500

def get_trustee_info(county, township):
    trustee = find_trustee_by_location(county, township)
    if trustee:
        return jsonify({
            "county": county,
            "township": township,
            "trustee": trustee
        })
    return jsonify({
        "county": county,
        "message": "No immediate trustee found for the provided address"
    })

@app.route('/townships', methods=['GET'])
def get_townships():
    county = request.args.get('county')
    if not county:
        return jsonify({"error": "County parameter is required"}), 400

    townships = set()
    for trustee in trustee_data_cache:
        if trustee['County'].lower() == county.lower():
            name = trustee['Name']
            township_name = name.replace(' Township Trustee', '').replace(' Trustee', '')
            townships.add(township_name)

    return jsonify({"townships": sorted(list(townships))})

@app.route('/trustee-lookup', methods=['GET'])
def trustee_lookup():
    county = request.args.get('county')
    township = request.args.get('township')

    if not county or not township:
        return jsonify({"error": "County and township are required"}), 400

    trustee = find_trustee_by_location(county, township)
    if trustee:
        return jsonify({"trustee": trustee})

    return jsonify({"error": "No trustee found for that county/township"}), 404

@app.route('/county-resources', methods=['GET'])
def county_resources():
    county = request.args.get('county')
    filter_type = request.args.get('filter', 'all')

    if not county:
        return jsonify({"error": "County parameter is required"}), 400

    response_data = {}

    if filter_type in ['all', 'trustee']:
        trustees = [t for t in trustee_data_cache if t['County'] == county]
        response_data['trustees'] = trustees

    if filter_type in ['all', 'food_pantry']:
        food_pantries = find_food_pantries_by_county(county)
        response_data['food_pantries'] = food_pantries

    return jsonify(response_data)

@app.route('/reverse-geocode', methods=['GET'])
def reverse_geocode():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required"}), 400

    is_valid, result = validate_coordinates(lat, lon)
    if not is_valid:
        return jsonify({"error": result}), 400

    latitude, longitude = result

    try:
        county, township = get_township(latitude, longitude)

        if not county or not township:
            return jsonify({"error": "No township found for the provided coordinates"}), 404

        trustee_info = find_trustee_by_location(county, township)
        food_pantries = find_food_pantries_by_county(county)

        return jsonify({
            "trustee": trustee_info,
            "food_pantries": food_pantries
        })

    except Exception as e:
        app.logger.exception('Unexpected error in reverse-geocode for lat=%s, lon=%s', lat, lon)
        return jsonify({"error": "An unexpected error occurred"}), 500


if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT)
