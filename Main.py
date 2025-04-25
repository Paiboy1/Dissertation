import subprocess
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Run the weather and events API scripts first
subprocess.run(["python", "Weather_API.py"])
subprocess.run(["python", "Events_API.py"])

# Load datasets
df = pd.read_csv("main_data.csv")
weather_df = pd.read_csv("datasets/cardiff_weather_forecast.csv")
events_df = pd.read_csv("datasets/cardiff_events.csv")

# Define rush hour periods (weekdays + key hours)
rush_hours = [7, 8, 9, 15, 16, 17]
weekdays = [0, 1, 2, 3, 4]

# Add binary rush_hour feature
df["rush_hour"] = df.apply(lambda row: 1 if row["day_of_week"] in weekdays and row["hour"] in rush_hours else 0, axis=1)

# Define features and target 
target = "all_motor_vehicles"
features = ["hour", "road_type_major", "road_type_minor", "weather_encoded", "hour_weight", "rush_hour"]

# Handle events
events_df["Date"] = pd.to_datetime(events_df["Date"]).dt.date
event_dates = set(events_df["Date"])
df["count_date"] = pd.to_datetime(df["count_date"], dayfirst=True)
df["event_day"] = df["count_date"].dt.date.apply(lambda d: 1 if d in event_dates else 0)

x = df[features]
y = df[target]

# Split into train/test using latest year per road
latest_years = df.groupby("count_point_id")["year"].max()
train_data = df[df.apply(lambda row: row["year"] < latest_years[row["count_point_id"]], axis=1)]
test_data = df[df.apply(lambda row: row["year"] == latest_years[row["count_point_id"]], axis=1)]

X_train, y_train = train_data[features], train_data[target]
X_test, y_test = test_data[features], test_data[target]

# Train the Random Forest model
rf_model = RandomForestRegressor(n_estimators=500, random_state=500)
rf_model.fit(X_train, y_train)

# Predict future traffic using count_point_id for context
def predict_future_traffic(count_point_id, date_str, hour):
    date = pd.to_datetime(date_str, format="%d/%m/%Y")

    # Weather lookup (uses cardiff_weather_forecast.csv)
    weather_df["Date"] = pd.to_datetime(weather_df["Date"]).dt.date
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

    event_today = events_df[
        (events_df["Date"] == date.date()) &
        (events_df["Road Name"].str.upper() == road_name_input.upper())
    ]

    # Find if there is a event
    event_day = 0
    if not event_today.empty:
        event_time_str = event_today.iloc[0]["Time"]
        event_hour = int(event_time_str.split(":")[0])
        if event_hour - 1 <= hour <= event_hour + 2:
            event_day = int(event_today.iloc[0]["event_day"]) 
            event_name = event_today.iloc[0]["Event Name"]
    
    rush_hour = 0
    if date.weekday() in [0, 1, 2, 3, 4] and hour in [7, 8, 9, 15, 16, 17]:
        rush_hour = 1

    # Input row
    input_row = {
        "hour": hour,
        "road_type_major": road_type_major,
        "road_type_minor": road_type_minor,
        "weather_encoded": weather_encoded,
        "hour_weight": hour_weight,
        "rush_hour": rush_hour,
    }

    input_df = pd.DataFrame([input_row])
    prediction = rf_model.predict(input_df)[0]

    print(f"\nPredicted traffic on the {count_point_id} for {date_str} at {hour}:00 → {prediction:.0f} vehicles.")

    if event_day == 1:
        prediction *= 1.15
        print(f"\nThis event '{event_name}' is on at {event_hour}:00 — expect increased traffic.")
    elif not event_today.empty:
        print("\nAn event is on today, but not during the selected time.")
    else:
        print("\nNo event on today.")

# Show feature importance (testing)
importances = rf_model.feature_importances_
feature_names = X_train.columns

plt.figure(figsize=(10, 6))
plt.barh(feature_names, importances)
plt.xlabel("Feature Importance")
plt.title("Random Forest Feature Importance")
plt.show()

# Make predictions on the test set
y_pred = rf_model.predict(X_test)

# Evaluate performance
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"R² Score: {r2:.2f}")

# User input loop
while True:
    road_name_input = input("Enter the road name (e.g., A48): ")
    date_input = input("Enter the date (DD/MM/YYYY): ")
    hour_input = int(input("Enter hour of day (7–18): "))
    predict_future_traffic(road_name_input, date_input, hour_input)
    print()