import googlemaps
import json

# Replace with your Google Maps API key
gmaps = googlemaps.Client(key='YOUR_API_KEY') #yes this should be an environment file. don't judge me.

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

for county in indiana_counties:
    search_query = f"township trustee office {county}, Indiana"
    places_result = gmaps.places(search_query)

    for place in places_result['results']:
        place_info = {
            "County": county,
            "Name": place.get('name', 'N/A'),
            "Address": place.get('formatted_address', 'N/A'),
            "Phone": 'N/A',  
            "Website": place.get('website', 'N/A'),
            "Latitude": place['geometry']['location']['lat'],
            "Longitude": place['geometry']['location']['lng']
        }

        # --- Place Details Request (gets phone and hours) --- 
        place_details = gmaps.place(place_id=place['place_id'])
        if 'formatted_phone_number' in place_details['result']:
            place_info["Phone"] = place_details['result']['formatted_phone_number']

        # Get opening hours from Place Details
        if 'opening_hours' in place_details['result']:
            place_info["Hours"] = place_details['result']['opening_hours'].get('weekday_text', 'N/A')
        else:
            place_info["Hours"] = 'N/A'

        all_township_data.append(place_info)

# Save data to a JSON file
with open("indiana_township_trustees.json", "w") as f:
    json.dump(all_township_data, f, indent=4)

print("Data saved to indiana_township_trustees.json")
