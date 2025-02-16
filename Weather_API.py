import requests

# OpenWeather API Key
API_KEY = "2ab92b6d1897d4e1cf8f50ab29b54a59"

# Cardiff coordinates
LAT, LON = 51.4816, -3.1791

# OpenWeather API URL for 5-day forecast (3-hour intervals)
url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

# Send API request
response = requests.get(url)

# Check if request was successful
if response.status_code == 200:
    weather_data = response.json()

    print("5-Day Weather Forecast for Cardiff (every 3 hours):\n")

    for forecast in weather_data["list"]:
        timestamp = forecast["dt_txt"]  # Date & time of forecast
        temp = forecast["main"]["temp"]  # Temperature in Celsius
        condition = forecast["weather"][0]["description"]  # Weather condition

        print(f"Time: {timestamp}, Temperature: {temp}°C, Condition: {condition}")