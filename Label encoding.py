import pandas as pd
from sklearn.preprocessing import LabelEncoder

file_path = "updated_with_label_encoding.csv"  
df = pd.read_csv(file_path, low_memory=False)

# Apply Label Encoding to weather
label_encoder = LabelEncoder()
df["weather_encoded"] = label_encoder.fit_transform(df["weather"])  

df.to_excel("updated_with_weather_encoding.xlsx", index=False)