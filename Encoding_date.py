import pandas as pd

# Load dataset
df = pd.read_csv("main_data.csv")

# Convert 'count_date' from DD/MM/YYYY to a datetime object
df["count_date"] = pd.to_datetime(df["count_date"], format="%d/%m/%Y")

# Extract useful date features
df["year"] = df["count_date"].dt.year
df["month"] = df["count_date"].dt.month
df["day_of_week"] = df["count_date"].dt.weekday  # Monday=0, Sunday=6
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)  # 1 for Sat/Sun, 0 for Mon-Fri

# Drop the original 'count_date' column (since it's now encoded)
df.drop(columns=["count_date"], inplace=True)

# Save the updated dataset
df.to_csv("processed_traffic_data.csv", index=False)