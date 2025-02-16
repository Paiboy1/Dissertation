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
        self.node_store = node_store  # Store reference to nodes
        self.excluded_types = {
            "footway", "steps", "service", "path", "bridleway", 
            "track", "cycleway", "pedestrian"
        }  # Excluded road types
        self.road_data = []  # List to store extracted road details

    def way(self, w):
        if "highway" in w.tags and len(w.nodes) > 0:
            road_type = w.tags["highway"]

            # Skip unwanted road types
            if road_type in self.excluded_types:
                return

            road_name = w.tags.get("name", "Unnamed Road")
            first_valid_location = None

            # Find first valid node within Cardiff
            for node in w.nodes:
                node_id = node.ref
                if node_id in self.node_store.node_locations:
                    lat, lon = self.node_store.node_locations[node_id]

                    # Check if location is within Cardiff bounding box
                    if 51.40 <= lat <= 51.55 and -3.25 <= lon <= -3.05:
                        first_valid_location = (lat, lon)
                        break  # Stop after finding first valid node in Cardiff

            if first_valid_location:
                lat, lon = first_valid_location
                self.road_data.append({"Road Name": road_name, "Type": road_type, "Latitude": lat, "Longitude": lon})

def main(osm_file):
    node_store = NodeStore()
    node_store.apply_file(osm_file)  # Extract node locations first

    handler = RoadExtractor(node_store)
    handler.apply_file(osm_file)  # Now process roads using valid node locations

    # Convert extracted data to a DataFrame
    df = pd.DataFrame(handler.road_data)

    # Save DataFrame to an Excel file
    df.to_excel("cardiff_roads.xlsx", index=False)

    print("✅ Saved Cardiff roads to cardiff_roads.xlsx!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <osm_file>")
        sys.exit(1)

    osm_file = sys.argv[1]
    main(osm_file)