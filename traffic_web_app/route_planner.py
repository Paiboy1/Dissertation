import osmnx as ox
import pandas as pd
import networkx as nx
import folium
import pickle
import subprocess
from flask import request
import sys

# Extract inputs from app.py
if __name__ == '__main__':
    start = sys.argv[1]
    end = sys.argv[2]
    date_input = sys.argv[3]
    hour_input = sys.argv[4]

subprocess.run([sys.executable, "traffic_web_app/Main.py", date_input, hour_input])

# Load Cardiff graph
custom_filter = (
    '"highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified"'
)
G = ox.graph_from_place("Cardiff, Wales, UK", network_type='drive')

# Load your main dataset
df = pd.read_csv('traffic_web_app/Datasets/main_data.csv')

with open('traffic_web_app/pkl/congestion_predictions.pkl', 'rb') as f:
    congestion_predictions = pickle.load(f)
with open('traffic_web_app/pkl/rush_hour.pkl', 'rb') as f:
    rush_hour = pickle.load(f)

# Mapping count_point_id to nearest node 
lons = df['longitude'].values
lats = df['latitude'].values
count_ids = df['count_point_id'].values
nearest_nodes = ox.distance.nearest_nodes(G, X=lons, Y=lats)
count_point_to_node = dict(zip(count_ids, nearest_nodes))
node_to_count_point = {v: k for k, v in count_point_to_node.items()}

def run_route_planner(start_location, end_location, date_input, hour_input):
    # Assign travel time (seconds) as weight 
    for u, v, key, data in G.edges(keys=True, data=True):
        count_point_u = node_to_count_point.get(u, None)
        count_point_v = node_to_count_point.get(v, None)

        # Default congestion and speed fallback
        congestion = 0
        base_speed_mph = 30  

        # Lookup predicted congestion
        if count_point_u in congestion_predictions and count_point_v in congestion_predictions:
            congestion = (congestion_predictions[count_point_u] + congestion_predictions[count_point_v]) / 2
        elif count_point_u in congestion_predictions:
            congestion = congestion_predictions[count_point_u]
        elif count_point_v in congestion_predictions:
            congestion = congestion_predictions[count_point_v]

        # Lookup speed limit
        speed_mph = base_speed_mph  
        if 'maxspeed' in data:
            maxspeed = data['maxspeed']
            if isinstance(maxspeed, list):
                maxspeed = maxspeed[0]
            if isinstance(maxspeed, str):
                if 'mph' in maxspeed and maxspeed.replace('mph', '').strip().isdigit():
                    speed_mph = int(maxspeed.replace('mph', '').strip())
                elif maxspeed.strip().isdigit():
                    speed_mph = int(maxspeed.strip())
            elif isinstance(maxspeed, (int, float)):
                speed_mph = float(maxspeed)

        # Adjust speed based on congestion
        congestion_factor = min(congestion / 1000, 1)
        adjusted_speed_mph = speed_mph * (1 - 0.5 * congestion_factor)
        if rush_hour == 1:
            adjusted_speed_mph *= 0.5

        # Calculate travel time in seconds
        if 'length' in data and adjusted_speed_mph > 0:
            distance_meters = data['length']
            distance_miles = distance_meters / 1609.34  
            travel_time_hours = distance_miles / adjusted_speed_mph
            travel_time_sec = travel_time_hours * 3600  
            data['travel_time'] = travel_time_sec

    # Find shortest route based on congestion using Djikstra
    start_point = ox.geocode(start_location)
    end_point = ox.geocode(end_location)

    orig_node = ox.distance.nearest_nodes(G, X=start_point[1], Y=start_point[0])
    dest_node = ox.distance.nearest_nodes(G, X=end_point[1], Y=end_point[0])

    route = nx.shortest_path(G, orig_node, dest_node, weight='travel_time')

    # Create Folium map 
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

        # Also include travel time
        if 'travel_time' in edge:
            total_time_sec += edge['travel_time']

    # Set markers for start and end locations
    folium.Marker(location=[start_point[0], start_point[1]], popup='Start', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=[end_point[0], end_point[1]], popup='End', icon=folium.Icon(color='red')).add_to(m)

    # Save to html for now for visualization
    m.save('traffic_web_app/static/route.html')
    total_time_min = total_time_sec / 60

    # Return travel time
    return round(total_time_min, 1)

if __name__ == "__main__":
    run_route_planner(start, end, date_input, int(hour_input))

    # call the function
    travel_time = run_route_planner(start, end, date_input, hour_input)
    print(travel_time)
