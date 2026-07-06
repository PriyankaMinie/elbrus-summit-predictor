# explore openmeteo_raw and compare it with era5 before building features
import pandas as pd
import numpy as np
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

dataset = pd.read_sql("SELECT * FROM openmeteo_raw", conn)
df_era5 = pd.read_sql("SELECT * FROM era5_cleaned", conn)
conn.close()
print(dataset)

print(dataset.shape)
print(dataset.dtypes)
print(dataset.isnull().sum())

print("Duplicate timestamps:", dataset["timestamp"].duplicated().sum())

print(
    dataset[
        ["temperature_c", "wind_speed_kmh", "precipitation_mm", "snowfall_cm"]
    ].describe()
)

print("=== ERA5 CLEANED ===")
print(df_era5.shape)
print(df_era5["timestamp"].duplicated().sum())
print(
    df_era5[
        ["temperature_c", "wind_speed_kmh", "precipitation_mm", "snowfall_cm"]
    ].describe()
)

df_openmeteo = dataset.set_index("timestamp")

daily_temp = df_openmeteo["temperature_c"].resample("D").min()
daily_wind = df_openmeteo["wind_speed_kmh"].resample("D").max()
daily_precip = df_openmeteo["precipitation_mm"].resample("D").max()
daily_snow = df_openmeteo["snowfall_cm"].resample("D").max()

# Aggregate openmeteo_raw from hourly to daily.
df_openmeteo_daily = pd.concat(
    [daily_temp, daily_wind, daily_precip, daily_snow], axis=1
)  # axis=1 means combine side by side as columns, not stack as more rows.

df_openmeteo_daily = df_openmeteo_daily.dropna()

print(df_openmeteo_daily)
