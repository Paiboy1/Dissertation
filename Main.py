import subprocess
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle

# --- 1. Run other scripts ---
subprocess.run(["python", "Weather_API.py"])
subprocess.run(["python", "Events_API.py"])

# --- 2. Load datasets ---
df = pd.read_csv("main_data.csv")
weather_df = pd.read_csv("datasets/cardiff_weather_forecast.csv")
events_df = pd.read_csv("datasets/cardiff_events.csv")

# Add historical weight (average vehicles per count_point_id)
avg_traffic = df.groupby('count_point_id')["all_motor_vehicles"].mean()
df["historical_weight"] = df["count_point_id"].map(avg_traffic)

# --- 3. Prepare features ---
rush_hours = [7, 8, 9, 15, 16, 17]
weekdays = [0, 1, 2, 3, 4]

df["rush_hour"] = df.apply(lambda row: 1 if row["day_of_week"] in weekdays and row["hour"] in rush_hours else 0, axis=1)

target = "all_motor_vehicles"
features = ["hour", "weather_encoded", "hour_weight", "rush_hour", "historical_weight"]

# --- 4. Handle events ---
events_df["Date"] = pd.to_datetime(events_df["Date"]).dt.date
event_dates = set(events_df["Date"])
df["count_date"] = pd.to_datetime(df["count_date"], dayfirst=True)
df["event_day"] = df["count_date"].dt.date.apply(lambda d: 1 if d in event_dates else 0)

x = df[features]
y = df[target]

# Split train/test
latest_years = df.groupby("count_point_id")["year"].max()
train_data = df[df.apply(lambda row: row["year"] < latest_years[row["count_point_id"]], axis=1)]
test_data = df[df.apply(lambda row: row["year"] == latest_years[row["count_point_id"]], axis=1)]

X_train, y_train = train_data[features], train_data[target]
X_test, y_test = test_data[features], test_data[target]

# --- 5. Train model ---
rf_model = RandomForestRegressor(n_estimators=500, random_state=500)
rf_model.fit(X_train, y_train)

# --- 6. Predict future traffic for all roads ---
def predict_all_roads(date_str, hour):
    date = pd.to_datetime(date_str, format="%d/%m/%Y")

    # Preprocess the weather
    weather_df["Date"] = pd.to_datetime(weather_df["Date"]).dt.date
    available = weather_df[weather_df["Date"] == date.date()]
    if available.empty:
        print("No weather forecast found for this date.")
        return {}

    # Pick closest weather hour if exact match not found
    if hour in available["Hour"].values:
        weather_row = available[available["Hour"] == hour].iloc[0]
    else:
        closest_hour = min(available["Hour"].values, key=lambda h: abs(h - hour))
        weather_row = available[available["Hour"] == closest_hour].iloc[0]

    weather_encoded = int(weather_row["weather_encoded"])

    # Predict congestion for every count point individually
    congestion_predictions = {}

    for count_point_id, group in df.groupby("count_point_id"):
        try:
            historical_weight = group["historical_weight"].mean()
            hour_weight = group[group["hour"] == hour]["hour_weight"].mode()[0]

            rush_hour = 0
            if date.weekday() in [0, 1, 2, 3, 4] and hour in [7, 8, 9, 15, 16, 17]:
                rush_hour = 1

            input_row = {
                "hour": hour,
                "weather_encoded": weather_encoded,
                "hour_weight": hour_weight,
                "rush_hour": rush_hour,
                "historical_weight": historical_weight,
            }

            input_df = pd.DataFrame([input_row])
            prediction = rf_model.predict(input_df)[0]

            congestion_predictions[count_point_id] = prediction

        except Exception as e:
            print(f"Skipping {count_point_id} due to error: {e}")
            continue

    return congestion_predictions

# --- 7. Feature importance ---
importances = rf_model.feature_importances_
feature_names = X_train.columns

plt.figure(figsize=(10, 6))
plt.barh(feature_names, importances)
plt.xlabel("Feature Importance")
plt.title("Random Forest Feature Importance")
plt.show()

# --- 8. Model evaluation ---
y_pred = rf_model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\nModel Performance:")
print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"R² Score: {r2:.2f}\n")

# --- 9. User input ---
date_input = input("Enter the date (DD/MM/YYYY): ")
hour_input = int(input("Enter hour of day (7–18): "))

# Save the returned predictions
congestion_predictions = predict_all_roads(date_input, hour_input)
with open('congestion_predictions.pkl', 'wb') as f:
    pickle.dump(congestion_predictions, f)