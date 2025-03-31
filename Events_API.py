import requests
import pandas as pd

# Ticketmaster API key
API_KEY = 'laqOtiGgIx9rzAEAr4JUWj9an9uR9eWL'

# API URL with Cardiff's coordinates
url = 'https://app.ticketmaster.com/discovery/v2/events.json'
params = {
    'latlong': '51.4816,-3.1791',
    'radius': '10',
    'unit': 'km',
    'apikey': API_KEY
}

# Mapping venues to known nearby roads
venue_to_road = {
    "Principality Stadium": "A4161",
    "St David's Hall": "A4161",
    "Utilita Arena Cardiff": "A4160",
    "Cardiff City Stadium": "B4267",
    "Sophia Gardens": "Secondary Roads",
    "Wales Millennium Centre": "A4119",
    "Motorpoint Arena Cardiff": "A4161",
    "New Theatre Cardiff": "A4161",
    "The Great Hall - Cardiff University Students' Union": "Secondary Road",
    "Fuel Rock Club": "Secondary Road",
    "Cardiff Arms Park": "Secondary Road"
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    events = data.get('_embedded', {}).get('events', [])
    event_list = []

    for event in events:
        name = event.get('name', 'No event name')
        start_date = event.get('dates', {}).get('start', {}).get('localDate', 'No date')
        venue = event.get('_embedded', {}).get('venues', [{}])[0].get('name', 'No venue')
        road = venue_to_road.get(venue, "Unknown")
        
        print(f"Event: {name}\nDate: {start_date}\nVenue: {venue}\nRoad: {road}\n")
        event_list.append([name, start_date, venue, road])
    
    df = pd.DataFrame(event_list, columns=["Event Name", "Date", "Venue", "Road Name"])
    df.to_csv("datasets/cardiff_events.csv", index=False)
    print("Events saved to cardiff_events.csv")