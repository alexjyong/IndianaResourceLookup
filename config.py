"""
Configuration settings for Indiana Resource Lookup application
"""

# Data file paths
DATA_DIR = 'static/utilities/data'
TRUSTEE_DATA_FILE = f'{DATA_DIR}/indiana_township_trustees.json'
FOOD_PANTRY_FILE = f'{DATA_DIR}/indiana_food_pantries.json'
TOWNSHIP_GEO_FILE = f'{DATA_DIR}/indiana_townships.geojson'
COUNTY_BBOX_FILE = f'{DATA_DIR}/counties_bounding_boxes.json'

# External API settings
NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_USER_AGENT = 'Indiana Resource Lookup'
NOMINATIM_TIMEOUT = 10  # seconds

# Indiana geographic bounds (for validation)
INDIANA_LAT_MIN = 37.8
INDIANA_LAT_MAX = 41.8
INDIANA_LON_MIN = -88.1
INDIANA_LON_MAX = -84.8

# Flask server settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
