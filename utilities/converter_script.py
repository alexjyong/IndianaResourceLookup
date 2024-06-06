import osmium as osm
import json

class AddressHandler(osm.SimpleHandler):
    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.addresses = []

    def node(self, n):
        if 'addr:housenumber' in n.tags and 'addr:street' in n.tags:
            address = {
                'type': 'node',
                'id': n.id,
                'latitude': n.location.lat,
                'longitude': n.location.lon,
                'housenumber': n.tags.get('addr:housenumber'),
                'street': n.tags.get('addr:street'),
                'city': n.tags.get('addr:city'),
                'state': n.tags.get('addr:state'),
                'postcode': n.tags.get('addr:postcode')
            }
            self.addresses.append(address)

    def way(self, w):
        if 'addr:housenumber' in w.tags and 'addr:street' in w.tags:
            address = {
                'type': 'way',
                'id': w.id,
                'nodes': [n.ref for n in w.nodes],
                'housenumber': w.tags.get('addr:housenumber'),
                'street': w.tags.get('addr:street'),
                'city': w.tags.get('addr:city'),
                'state': w.tags.get('addr:state'),
                'postcode': w.tags.get('addr:postcode')
            }
            self.addresses.append(address)

def save_addresses_to_json(addresses, filename):
    with open(filename, 'w') as f:
        json.dump(addresses, f, indent=4)

def main(osm_file, output_file):
    handler = AddressHandler()
    handler.apply_file(osm_file)

    save_addresses_to_json(handler.addresses, output_file)
    print(f"Extracted {len(handler.addresses)} addresses and saved to {output_file}")

if __name__ == "__main__":
    osm_file = "data/indiana.pbf"  # Update this to the correct path
    output_file = "data/indiana_addresses2.json"
    main(osm_file, output_file)
