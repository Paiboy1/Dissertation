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

class BuildingExtractor(osmium.SimpleHandler):
    def __init__(self, node_store):
        super().__init__()
        self.node_store = node_store  
        self.excluded_types = {"shed", "garage", "container", "greenhouse"} 
        self.building_data = []  

    def way(self, w):
        if "building" in w.tags and len(w.nodes) > 0:
            building_type = w.tags["building"]
            building_name = w.tags.get("name", "Unnamed Building")

            # Skip buildings where BOTH names is "Unnamed Building" AND type is "yes"
            if building_name == "Unnamed Building" and building_type == "yes":
                return

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
                self.building_data.append({"Building Name": building_name, "Type": building_type, "Latitude": lat, "Longitude": lon})

def main(osm_file):
    node_store = NodeStore()
    node_store.apply_file(osm_file)  

    handler = BuildingExtractor(node_store)
    handler.apply_file(osm_file)  

    df = pd.DataFrame(handler.building_data)

    # Save to Excel
    df.to_excel("cardiff_buildings.xlsx", index=False)

    print("Saved Cardiff buildings")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <osm_file>")
        sys.exit(1)

    osm_file = sys.argv[1]
    main(osm_file)