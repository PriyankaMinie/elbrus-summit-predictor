import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Load era5_cleaned
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

df_era5 = pd.read_sql("SELECT * FROM era5_cleaned ORDER BY timestamp", conn)

# Feature engineering
df_era5["wind_chill"] = (
    13.12
    + 0.6215 * df_era5["temperature_c"]
    - 11.37 * (df_era5["wind_speed_kmh"] ** 0.16)
    + 0.3965 * df_era5["temperature_c"] * (df_era5["wind_speed_kmh"] ** 0.16)
)
df_era5["wind_lag_1"] = df_era5["wind_speed_kmh"].shift(1)
df_era5["temp_lag_1"] = df_era5["temperature_c"].shift(1)
df_era5 = df_era5.dropna(subset=["wind_lag_1", "temp_lag_1"])

# Insert into features_daily
cursor = conn.cursor()

for _, row in df_era5.iterrows():
    cursor.execute(
        """
        INSERT INTO features_daily (timestamp, temperature_c, wind_speed_kmh, precipitation_mm, snowfall_cm, wind_chill, wind_lag_1, temp_lag_1, is_climbable)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
        (
            row["timestamp"],
            row["temperature_c"],
            row["wind_speed_kmh"],
            row["precipitation_mm"],
            row["snowfall_cm"],
            row["wind_chill"],
            row["wind_lag_1"],
            row["temp_lag_1"],
            row["climbable"],
        ),
    )

conn.commit()
cursor.close()
conn.close()
print("features_daily loaded successfully")
