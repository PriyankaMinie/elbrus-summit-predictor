import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
df_era5 = pd.read_sql("SELECT * FROM era5_cleaned ORDER BY timestamp", conn)
conn.close()


# wind_chill = 13.12 + 0.6215*T - 11.37*(V**0.16) + 0.3965*T*(V**0.16)
df_era5["wind_chill"] = (
    13.12
    + 0.6215 * df_era5["temperature_c"]
    - 11.37 * (df_era5["wind_speed_kmh"] ** 0.16)
    + 0.3965 * df_era5["temperature_c"] * (df_era5["wind_speed_kmh"] ** 0.16)
)

# The _1 specifically means lag of 1 day — i.e., yesterday. This naming convention matters if you ever want to add more lag features late
df_era5["wind_lag_1"] = df_era5["wind_speed_kmh"].shift(1)
df_era5["temp_lag_1"] = df_era5["temperature_c"].shift(1)

print(df_era5.isnull().sum())

# dropping NaN(1st row has NaN wind_lag_1 and temp_lag_1)
df_era5 = df_era5.dropna(subset=["wind_lag_1", "temp_lag_1"])

print(df_era5.head())
print(df_era5.shape)
