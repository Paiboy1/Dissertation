import osmnx as ox
import pandas as pd
import networkx as nx
import folium
import pickle
import subprocess

subprocess.run(["python", "Main.py"])

# Load Cardiff graph
custom_filter = (
    '"highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified"'
)
G = ox.graph_from_place("Cardiff, Wales, UK", network_type='drive')

# Load your main dataset
df = pd.read_csv('main_data.csv')

with open('congestion_predictions.pkl', 'rb') as f:
    congestion_predictions = pickle.load(f)

# --- Step 1: Build mapping count_point_id -> nearest node ---
lons = df['longitude'].values
lats = df['latitude'].values
count_ids = df['count_point_id'].values
nearest_nodes = ox.distance.nearest_nodes(G, X=lons, Y=lats)
count_point_to_node = dict(zip(count_ids, nearest_nodes))
node_to_count_point = {v: k for k, v in count_point_to_node.items()}

# --- Step 2: Ask user for journey info ---
start_location = input("Enter starting location: ")
end_location = input("Enter ending location: ")

# --- Step 4: Assign travel time (seconds) as weight ---
for u, v, key, data in G.edges(keys=True, data=True):
    count_point_u = node_to_count_point.get(u, None)
    count_point_v = node_to_count_point.get(v, None)

    if count_point_u in congestion_predictions and count_point_v in congestion_predictions:
        congestion = (congestion_predictions[count_point_u] + congestion_predictions[count_point_v]) / 2
    elif count_point_u in congestion_predictions:
        congestion = congestion_predictions[count_point_u]
    elif count_point_v in congestion_predictions:
        congestion = congestion_predictions[count_point_v]
    else:
        congestion = 10000  # fallback if no prediction

    # Calculate speed
    base_speed_kmh = 50
    congestion_factor = min(congestion / 1000, 1)
    speed_kmh = base_speed_kmh * (1 - 0.5 * congestion_factor)
    speed_ms = speed_kmh * (1000/3600)

    if 'length' in data and speed_ms > 0:
        distance_m = data['length']
        travel_time_sec = distance_m / speed_ms
        data['travel_time'] = travel_time_sec

# --- Step 5: Find shortest route based on congestion ---
start_point = ox.geocode(start_location)
end_point = ox.geocode(end_location)

orig_node = ox.distance.nearest_nodes(G, X=start_point[1], Y=start_point[0])
dest_node = ox.distance.nearest_nodes(G, X=end_point[1], Y=end_point[0])

route = nx.shortest_path(G, orig_node, dest_node, weight='travel_time')

# --- Step 6: Create Folium map ---
m = folium.Map(location=start_point, zoom_start=14)

total_time_sec = 0

for u, v in zip(route[:-1], route[1:]):
    data = G.get_edge_data(u, v)
    if isinstance(data, dict):
        edge = data[list(data.keys())[0]]
    else:
        edge = data

    if 'geometry' in edge:
        points = [(point[1], point[0]) for point in edge['geometry'].coords]
    else:
        points = [(G.nodes[u]['y'], G.nodes[u]['x']), (G.nodes[v]['y'], G.nodes[v]['x'])]

    folium.PolyLine(points, color='red', weight=5).add_to(m)

    # Also accumulate travel time
    if 'travel_time' in edge:
        total_time_sec += edge['travel_time']

folium.Marker(location=[start_point[0], start_point[1]], popup='Start', icon=folium.Icon(color='green')).add_to(m)
folium.Marker(location=[end_point[0], end_point[1]], popup='End', icon=folium.Icon(color='red')).add_to(m)

m.save('route.html')
total_time_min = total_time_sec / 60
print(f"\n🛣️ Estimated travel time: {total_time_min:.1f} minutes")
