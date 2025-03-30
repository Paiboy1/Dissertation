import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# Load main dataset
file_path = "main_data.csv"
df = pd.read_csv(file_path)

#set target and features
target = "all_motor_vehicles"
features = ["count_point_id","month","day_of_week","hour","year","pedal_cycles","two_wheeled_motor_vehicles","cars_and_taxis","buses_and_coaches","lgvs","all_hgvs","road_type_major","road_type_minor","road_name_encoded","weather_encoded"]

x = df[features]
y= df[target]

# To split into training and testing data I have to take the most recent year from a road and use it for testing
latest_years = df.groupby("count_point_id")["year"].max()
train_data = df[df.apply(lambda row: row["year"] < latest_years[row["count_point_id"]], axis=1)]
test_data = df[df.apply(lambda row: row["year"] == latest_years[row["count_point_id"]], axis=1)]

X_train, y_train = train_data[features], train_data[target]
X_test, y_test = test_data[features], test_data[target]

# Start the Random Forest model
rf_model = RandomForestRegressor(n_estimators=100, random_state=100)

# Train the model
rf_model.fit(X_train, y_train)

# Predict using the trained model
y_pred = rf_model.predict(X_test)

def predict_traffic(count_point_id, date, hour):
    date = pd.to_datetime(date, format="%d/%m/%Y")

    # Extract necessary data
    year, month, day_of_week = date.year, date.month, date.weekday() 

    # Find matching rows 
    matching_rows = X_test[
        (X_test["count_point_id"] == count_point_id) &
        (X_test["year"] == year) & 
        (X_test["month"] == month) & 
        (X_test["day_of_week"] == day_of_week) & 
        (X_test["hour"] == hour)
    ]

    # Use the exact list from training
    features_predict = matching_rows[features] 

    # Predict the traffic
    prediction = rf_model.predict(features_predict).mean()

    # Get road name
    road_name = df[df["count_point_id"] == count_point_id]["road_name"].iloc[0]

    print(f"Predicted traffic on {road_name} ({count_point_id}) for {date.strftime('%d/%m/%Y')} at {hour}:00: {prediction:.0f} vehicles.")

predict_traffic(30631,"01/04/2019",12)

