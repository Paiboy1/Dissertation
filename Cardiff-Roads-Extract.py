import osmium
import sys
import pandas as pd

class NodeStore(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.node_locations = {}

    def node(self, n):
        if n.location.valid():
            self.node_locations[n.id] = (n.location.lat, n.location.lon)

class RoadExtractor(osmium.SimpleHandler):
    def __init__(self, node_store):
        super().__init__()
        self.node_store = node_store  
        self.excluded_types = {
            "footway", "steps", "service", "path", "bridleway", 
            "track", "cycleway", "pedestrian"
        }  
        self.road_data = []  

    def way(self, w):
        if "highway" in w.tags and len(w.nodes) > 0:
            road_type = w.tags["highway"]

            # Skip unwanted road types
            if road_type in self.excluded_types:
                return

            road_name = w.tags.get("name", "Unnamed Road")
            first_valid_location = None

            # Define Cardiff area
            for node in w.nodes:
                node_id = node.ref
                if node_id in self.node_store.node_locations:
                    lat, lon = self.node_store.node_locations[node_id]

                    if 51.40 <= lat <= 51.55 and -3.25 <= lon <= -3.05:
                        first_valid_location = (lat, lon)
                        break  

            if first_valid_location:
                lat, lon = first_valid_location
                self.road_data.append({"Road Name": road_name, "Type": road_type, "Latitude": lat, "Longitude": lon})

def main(osm_file):
    node_store = NodeStore()
    node_store.apply_file(osm_file)  

    handler = RoadExtractor(node_store)
    handler.apply_file(osm_file)  

    df = pd.DataFrame(handler.road_data)

    df.to_excel("cardiff_roads.xlsx", index=False)

    print("✅ Saved Cardiff roads to cardiff_roads.xlsx!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <osm_file>")
        sys.exit(1)

    osm_file = sys.argv[1]
    main(osm_file)