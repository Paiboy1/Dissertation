import requests
import pandas as pd

# Ticketmaster API key
API_KEY = '	laqOtiGgIx9rzAEAr4JUWj9an9uR9eWL'

# API URL with Cardiff's coordinates
url = 'https://app.ticketmaster.com/discovery/v2/events.json'
params = {
    'latlong': '51.4816,-3.1791',
    'radius': '10',
    'unit': 'km',
    'apikey': API_KEY
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
        print(f"Event: {name}\nDate: {start_date}\nVenue: {venue}\n")
        event_list.append([name, start_date, venue])
    
    df = pd.DataFrame(event_list, columns=["Event Name", "Date", "Venue"])

    df.to_excel("cardiff_events.xlsx", index=False)
    print("Events saved to cardiff_events.xlsx")
