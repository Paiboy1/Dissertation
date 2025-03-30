import requests
import pandas as pd

# OpenWeather API Key
API_KEY = "2ab92b6d1897d4e1cf8f50ab29b54a59"

# Cardiff coordinates
LAT, LON = 51.4816, -3.1791

# OpenWeather API URL
url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

response = requests.get(url)

def encode_weather(condition):
    condition = condition.lower()
    if "rain" in condition:
        return 2  # Rain
    elif "clear" in condition:
        return 0  # Clear
    else:
        return 1  # Cloudy

def get_hour_weight(hour):
    if hour in [7, 8, 9, 15, 16, 17]:
        return 3
    elif 10 <= hour <= 14 or hour == 18:
        return 2
    else:
        return 1

if response.status_code == 200:
    weather_data = response.json()

    print("5-Day Weather Forecast for Cardiff (every 3 hours):\n")

    forecast_list = []

    for forecast in weather_data["list"]:
        timestamp = forecast["dt_txt"]
        temp = forecast["main"]["temp"]
        condition = forecast["weather"][0]["description"]

        print(f"Time: {timestamp}, Temperature: {temp}°C, Condition: {condition}")
        forecast_list.append([timestamp, temp, condition])

    df = pd.DataFrame(forecast_list, columns=["Time", "Temperature (°C)", "Condition"])

    df["Time"] = pd.to_datetime(df["Time"])
    df["Date"] = df["Time"].dt.date
    df["Hour"] = df["Time"].dt.hour
    df = df.drop(columns=["Time"])

    df["weather_encoded"] = df["Condition"].apply(encode_weather)
    df["hour_weight"] = df["Hour"].apply(get_hour_weight)
    df["weather_hour_impact"] = df["weather_encoded"] * df["hour_weight"]

    df.to_csv("Datasets/cardiff_weather_forecast.csv", index=False)
    print("Weather forecast saved to cardiff_weather_forecast.csv")