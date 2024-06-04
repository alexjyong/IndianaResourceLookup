import googlemaps
import json


gmaps = googlemaps.Client(key='') 

indiana_counties = [
    "Adams", "Allen", "Bartholomew", "Benton", "Blackford", "Boone", "Brown",
    "Carroll", "Cass", "Clark", "Clay", "Clinton", "Crawford", "Daviess",
    "Dearborn", "Decatur", "DeKalb", "Delaware", "Dubois", "Elkhart",
    "Fayette", "Floyd", "Fountain", "Franklin", "Fulton", "Gibson",
    "Grant", "Greene", "Hamilton", "Hancock", "Harrison", "Hendricks",
    "Henry", "Howard", "Huntington", "Jackson", "Jasper", "Jay", "Jefferson",
    "Jennings", "Johnson", "Knox", "Kosciusko", "LaGrange", "Lake",
    "LaPorte", "Lawrence", "Madison", "Marion", "Marshall", "Martin",
    "Miami", "Monroe", "Montgomery", "Morgan", "Newton", "Noble",
    "Ohio", "Orange", "Owen", "Parke", "Perry", "Pike", "Porter",
    "Posey", "Pulaski", "Putnam", "Randolph", "Ripley", "Rush", "St. Joseph",
    "Scott", "Shelby", "Spencer", "Starke", "Steuben", "Sullivan",
    "Switzerland", "Tippecanoe", "Tipton", "Union", "Vanderburgh",
    "Vermillion", "Vigo", "Wabash", "Warren", "Warrick", "Washington",
    "Wayne", "Wells", "White", "Whitley"
]

all_township_data = []

def replace_unicode_spaces(data):
  """Recursively replaces Unicode spaces in strings within a data structure."""
  if isinstance(data, dict):
    return {key: replace_unicode_spaces(value) for key, value in data.items()}
  elif isinstance(data, list):
    return [replace_unicode_spaces(item) for item in data]
  elif isinstance(data, str):
    data = data.replace('\u202f', ' ')
    data = data.replace('\u2009', ' ')
    data = data.replace('\u2013', '-')
    return data
  else:
    return data

def is_location_in_county(lat, lng, county_name):
    """Checks if a given latitude and longitude are within a specific county."""
    geocode_result = gmaps.reverse_geocode((lat, lng))
    if geocode_result:
        address_components = geocode_result[0].get('address_components', [])
        for component in address_components:
            if "administrative_area_level_2" in component['types'] and component['long_name'] == f"{county_name} County":
                return True
    return False

for county in indiana_counties:
    search_query = f"township trustee office {county} County Indiana"
    places_result = gmaps.places(search_query)

    for place in places_result['results']:
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']

        if is_location_in_county(lat, lng, county):
            place_info = {
                "County": county,
                "Name": place.get('name', 'N/A'),
                "Address": place.get('formatted_address', 'N/A'),
                "Phone": 'N/A',  
                "Website": place.get('website', 'N/A'),
                "Latitude": lat,
                "Longitude": lng
            }

            # --- Place Details Request (gets phone and hours) --- 
            place_details = gmaps.place(place_id=place['place_id'])
            if 'formatted_phone_number' in place_details['result']:
                place_info["Phone"] = place_details['result']['formatted_phone_number']

            # Get opening hours from Place Details
            if 'opening_hours' in place_details['result']:
                place_info["Hours"] = place_details['result']['opening_hours'].get('weekday_text', 'N/A')

            # --- Clean up Unicode Spaces Before Saving ---
            place_info = replace_unicode_spaces(place_info) 
            all_township_data.append(place_info)

# Save data to a JSON file
with open("indiana_township_trustees.json", "w", encoding='utf-8') as f:
    json.dump(all_township_data, f, indent=4)

print("Data saved to indiana_township_trustees.json")