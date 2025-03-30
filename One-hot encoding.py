import pandas as pd

file_path = "datasets/updated_with_weather_data.csv"
df = pd.read_csv(file_path, low_memory=False)

# Apply One-Hot Encoding to road_type
df = pd.get_dummies(df, columns=["road_type"], prefix="road_type")

df.to_csv("processed_data.csv", index=False)

