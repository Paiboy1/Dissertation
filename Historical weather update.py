import pandas as pd
import requests
import time

# Load dataset
file_path = "filtered_street_counts.csv"
df = pd.read_csv(file_path, low_memory=False)

# Convert 'count_date' from DD/MM/YYYY to YYYY-MM-DD
date_column = "count_date"
df[date_column] = pd.to_datetime(df[date_column], format="%d/%m/%Y", errors="coerce")

# Replace with your actual API key
API_KEY = "S94NMJPDKYBH9HZV54WFCBAAV"
location = "Cardiff,UK"

# Create new 'weather' column
weather_column = "weather"
if weather_column not in df.columns:
    df[weather_column] = None

# Function to get weather for a given date
def get_weather(date):
    if pd.isna(date):
        return "Invalid Date"
    
    formatted_date = date.strftime("%Y-%m-%d")  # Convert to accepted API format

    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{formatted_date}?unitGroup=metric&include=days&key={API_KEY}&contentType=json"

    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json()
            if "days" in data and len(data["days"]) > 0:
                return data["days"][0]["conditions"] 
            else:
                return "No Data"
        except requests.exceptions.JSONDecodeError:
            return "JSON Error"
    else:
        return f"API Error {response.status_code}"

# Loop through dataset and fetch weather for each date
for index, row in df.iterrows():
    if pd.isna(row[weather_column]):  
        weather = get_weather(row[date_column])
        df.at[index, weather_column] = weather
        print(f"Updated: {row[date_column].strftime('%d/%m/%Y')} → {weather}")


updated_file_path = "updated_weather_data.csv"
df.to_csv(updated_file_path, index=False)