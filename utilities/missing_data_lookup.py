#searches google api for missing township information, if possible to find.
import json
import os
import googlemaps
from shapely.geometry import shape, Point

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def is_information_missing(trustee):
    return not trustee['Address'] or not trustee['Latitude'] or not trustee['Longitude']

def search_google_maps(gmaps, township_name, county_name):
    query = f"{township_name} office in {county_name} indiana"
    places_result = gmaps.places(query)
    if places_result['results']:
        return places_result['results'][0]
    return None

def is_within_township(township_shape, lat, lng):
    point = Point(lng, lat)
    return township_shape.contains(point)

def update_trustee_info(gmaps, trustee, township_shape):
    place = search_google_maps(gmaps, trustee['Name'], trustee['County'])
    if place:
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']

        if is_within_township(township_shape, lat, lng):
            trustee['Address'] = place.get('formatted_address', trustee['Address'])
            trustee['Latitude'] = lat
            trustee['Longitude'] = lng

            # Get place details for phone and hours
            place_id = place['place_id']
            place_details = gmaps.place(place_id=place_id)
            result = place_details['result']
            
            trustee['Phone'] = result.get('formatted_phone_number', trustee['Phone'])
            trustee['Website'] = result.get('website', trustee['Website'])
            trustee['Hours'] = result['opening_hours'].get('weekday_text', []) if 'opening_hours' in result else trustee['Hours']
    return trustee

def main():
    google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_api_key:
        print("Please set the GOOGLE_MAPS_API_KEY environment variable.")
        return

    gmaps = googlemaps.Client(key=google_api_key)

    trustee_file = '../static/utilities/data/indiana_township_trustees.json'
    geojson_file = '../static/utilities/data/indiana_townships.geojson'
    trustee_data = load_json(trustee_file)
    geojson_data = load_json(geojson_file)

    for feature in geojson_data['features']:
        township_shape = shape(feature['geometry'])
        township_name = feature['properties']['tl_2021_18_cousub_namelsad'].replace(' Township', '')
        county_name = feature['properties']['cnty_name']

        for trustee in trustee_data:
            if trustee['Name'].lower().startswith(township_name.lower()) and trustee['County'].lower() == county_name.lower():
                if is_information_missing(trustee):
                    trustee = update_trustee_info(gmaps, trustee, township_shape)

    save_json(trustee_data, trustee_file)
    print("Trustee information update complete.")

if __name__ == '__main__':
    main()
