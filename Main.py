import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import matplotlib.pyplot as plt

# Load datasets
df = pd.read_csv("main_data.csv")
weather_df = pd.read_csv("datasets/cardiff_weather_forecast.csv")

# Define features and target (no weather impact score)
target = "all_motor_vehicles"
features = ["month", "day_of_week", "hour", "year", "road_type_major", "road_type_minor", "weather_encoded", "hour_weight"]

x = df[features]
y = df[target]

# Split into train/test using latest year per road
latest_years = df.groupby("count_point_id")["year"].max()
train_data = df[df.apply(lambda row: row["year"] < latest_years[row["count_point_id"]], axis=1)]
test_data = df[df.apply(lambda row: row["year"] == latest_years[row["count_point_id"]], axis=1)]

X_train, y_train = train_data[features], train_data[target]
X_test, y_test = test_data[features], test_data[target]

# Train the Random Forest model
rf_model = RandomForestRegressor(n_estimators=100, random_state=100)
rf_model.fit(X_train, y_train)

# Predict future traffic using count_point_id for context
def predict_future_traffic(count_point_id, date_str, hour):
    date = pd.to_datetime(date_str, format="%d/%m/%Y")
    year, month, day_of_week = date.year, date.month, date.weekday()

    # Weather lookup (uses cardiff_weather_forecast.csv)
    weather_df["Date"] = pd.to_datetime(weather_df["Date"], dayfirst=True, format="%d/%m/%Y").dt.date
    available = weather_df[weather_df["Date"] == date.date()]
    if available.empty:
        print("No weather forecast found for this date.")
        return
    
    # If the hour entered as a input does not match a time in the dataset, it chooses the closest hour
    if hour in available["Hour"].values:
        row = available[available["Hour"] == hour].iloc[0]
    else:
        closest_hour = min(available["Hour"].values, key=lambda h: abs(h - hour))
        row = available[available["Hour"] == closest_hour].iloc[0]

    # Get the weather encode
    weather_encoded = int(row["weather_encoded"])

    # Get the hour weight
    hour_weight = df[df["hour"] == hour]["hour_weight"].mode()[0]

    # Extract road using road name
    road_data = df[df["road_name"].str.lower() == road_name_input.lower()]
    if road_data.empty:
        print("Road name not found.")
        return

    # Get the road type
    road_type_major = road_data["road_type_major"].mode()[0]
    road_type_minor = road_data["road_type_minor"].mode()[0]

    # Input row
    input_row = {
        "month": month,
        "day_of_week": day_of_week,
        "hour": hour,
        "year": year,
        "road_type_major": road_type_major,
        "road_type_minor": road_type_minor,
        "weather_encoded": weather_encoded,
        "hour_weight": hour_weight
    }

    input_df = pd.DataFrame([input_row])
    prediction = rf_model.predict(input_df)[0]

    print(f"Predicted traffic at Count Point {count_point_id} for {date_str} at {hour}:00 → {prediction:.0f} vehicles.")

# Show feature importance (testing)
importances = rf_model.feature_importances_
feature_names = X_train.columns

plt.figure(figsize=(10, 6))
plt.barh(feature_names, importances)
plt.xlabel("Feature Importance")
plt.title("Random Forest Feature Importance")
plt.show()

# User input loop
while True:
    road_name_input = input("Enter the road name (e.g., A48): ")
    date_input = input("Enter the date (DD/MM/YYYY): ")
    hour_input = int(input("Enter hour of day (0–23): "))
    predict_future_traffic(road_name_input, date_input, hour_input)
    print()