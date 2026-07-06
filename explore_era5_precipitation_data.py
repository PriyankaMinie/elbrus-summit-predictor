import netCDF4 as nc
import pandas as pd
import numpy as np

# We are only using index [1, 1] which is exactly 43.25°N, 42.25°E — the Elbrus coordinates.
# We don't need all 5x5 grid points because we only care about one specific location — Elbrus summit.
# Load the NetCDF file
dataset = nc.Dataset("era5_precipitation_raw.nc")
# print("Variables:", list(dataset.variables.keys()))
# print("\nDimensions:", list(dataset.dimensions.keys()))

# numpy multidimensional array slicing
tp = dataset.variables["tp"][:, 1, 1]
# print(f"tp: {tp}")
# print(f"Min precipitaion: {np.min(tp)}")
# print(f"Max precipitaion: {np.max(tp)}")
# print(f"Average precipitaion: {np.mean(tp)}")
# print(f"Negative values in tp: {np.sum(tp<0)}")
# print(f"Sample values in tp: {tp[:5]}")
# print(f"Null values in tp:{sum(np.isnan(tp))}")

sf = dataset.variables["sf"][:, 1, 1]
# print(f"sf: {sf}")
# print(f"Min snowfall: {np.min(sf)}")
# print(f"Max snowfall: {np.max(sf)}")
# print(f"Average snowfall: {np.mean(sf)}")
# print(f"Negative values in sf: {np.sum(sf<0)}")
# print(f"Sample values in sf: {sf[:5]}")
# print(f"Null values in sf:{sum(np.isnan(sf))}")

# check the units of the variables
# print(dataset.variables["tp"])
# print(dataset.variables["sf"])

# convert the variables into different units
# precipitation --> from meters to milimeters, snowfall --> from meters to cm, timestamps --> convert to tiimestamp
tp_raw = dataset.variables["tp"][:, 1, 1]
tp_mm = tp_raw * 1000
# print(tp_mm)

sf_raw = dataset.variables["sf"][:, 1, 1]
sf_cm = sf_raw * 100
# print(sf_cm)

time = dataset.variables["valid_time"][:]
timestamps = pd.to_datetime(time, unit="s")
# print(timestamps)

df = pd.DataFrame(
    {"timestamp": timestamps, "precipitation_mm": tp_mm, "snowfall_cm": sf_cm}
)
# print(df.head())

# Resampling - e.g --> "Group all hours belonging to July 1st together, then calculate min/max."
# setting index means "Stop using 0,1,2,3 as row identifier. Use timestamp instead.
df = df.set_index("timestamp")
# print(df.index)
# print(df.index.month.unique())

df_filtered = df[df.index.month.isin([7, 8])]
# print(df_filtered.index.month.unique())
# print(len(df_filtered))

daily_precipitation_summary = df_filtered["precipitation_mm"].resample("D").agg("max")
# print(daily_precipitation_summary)

daily_snowfall_summary = df_filtered["snowfall_cm"].resample("D").agg("max")
# print(daily_snowfall_summary)

# check in case of nulls after resampling
# print(daily_precipitation_summary.isnull().sum())
# print(daily_snowfall_summary.isnull().sum())

# dropping nulls
daily_precipitation_summary = daily_precipitation_summary.dropna()
daily_snowfall_summary = daily_snowfall_summary.dropna()
# print(daily_precipitation_summary)
# print(print(daily_snowfall_summary))

# pandas combine two series into dataframe
df = pd.concat([daily_precipitation_summary, daily_snowfall_summary], axis=1)
# print(df)

# Load existing temperature/wind dataset
df_existing = pd.read_csv("elbrus_daily_weather_2021_2022.csv")
# print(df_existing.columns)
# print(df_existing.head())
# When you do pd.read_csv(...), pandas reads the timestamp column as plain text strings — like "2021-07-01" — not as actual datetime objects.
df_existing["timestamp"] = pd.to_datetime(df_existing["timestamp"])
# set index
df_existing = df_existing.set_index("timestamp")
# df (your precipitation + snowfall combined dataframe from previous step)
# Join both on timestamp index
df_final = df_existing.join(df)

# print(df_final.head())
# print(df_final.shape)

# Re-Deriving "Climbable" column
df_final["climbable_new"] = np.where(
    (df_final["temperature_c"] < -20)
    | (df_final["wind_speed_kmh"] > 40)
    | (df_final["precipitation_mm"] > 1)
    | (df_final["snowfall_cm"] > 0.5),
    0,
    1,
)

# print(df_final)
# print(df_final["climbable_new"].value_counts())
# print(df_final[["climbable_new"]].head(20))
# print((df_final["climbable"] != df_final["climbable_new"]).sum())
# print(df_final[df_final["precipitation_mm"] > 1][["precipitation_mm", "climbable_new"]])
# print(df_final[df_final["snowfall_cm"] > 0.5][["snowfall_cm", "climbable_new"]])

# verify there are no nulls anywhere in the final dataframe
# print(df_final.columns)
# print(df_final.isnull().sum())

# drop 'climbable' column
df = df_final.drop(columns=["climbable"])
# print(df)

df = df.rename(columns={"climbable_new": "climbable"})
# print(df)

# Reset index so timestamp becomes a regular column again
df.reset_index(inplace=True)
df.to_csv("E:/Portfolio_Project/elbrus_daily_weather_full_2021_2022.csv", index=False)

print(df.head())
print(df.shape)
print(df.columns)
