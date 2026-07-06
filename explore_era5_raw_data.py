import netCDF4 as nc
import pandas as pd
import numpy as np

# Load the NetCDF file
dataset = nc.Dataset("era5_raw.nc")
print("Available variables:", list(dataset.variables.keys()))
pressure_levels = dataset.variables["pressure_level"][:]
print("Pressure levels available:", pressure_levels)
print("Index 0 pressure level:", pressure_levels[0])

# Print dataset
# print(dataset.variables["t"])

# verify co-ordinates
latitudes = dataset.variables["latitude"][:]
longitudes = dataset.variables["longitude"][:]

# print(f"latitudes: {latitudes}")
# print(f"longitudes: {longitudes}")

# verify temperature, u-wind and v-wind sample at Elbrus

time = dataset.variables["valid_time"][:]
temp = dataset.variables["t"][:, 0, 3, 1]
u_wind = dataset.variables["u"][:, 0, 3, 1]
v_wind = dataset.variables["v"][:, 0, 3, 1]


# print(f"temperature sample: {temp}")
# print(f"u_wind sampla: {u_wind}")
# print(f"v_wind sample: {v_wind}")

# print(dataset.variables["u"])

df = pd.DataFrame(
    {"time": time, "temperature_k": temp, "u_wind": u_wind, "v_wind": v_wind}
)

# Data cleansing - deriving needed columns from available columns & dropping unnecessary columns

df["timestamp"] = pd.to_datetime(df["time"], unit="s")
df["temperature_c"] = df["temperature_k"] - 273.15
df["wind_speed_kmh"] = np.sqrt(df["u_wind"] ** 2 + df["v_wind"] ** 2) * 3.6
df = df.drop(columns=["time", "temperature_k", "u_wind", "v_wind"])

# Deriving "Climbable" column
df["climbable"] = np.where(
    (df["temperature_c"] < -20) | (df["wind_speed_kmh"] > 40), 0, 1
)

# Printing the output to check if the data is the derived logic is working

# print(df.head(10))  # df.head()  → method (an action that does something)
print(
    df["climbable"].value_counts()
)  # counts how many times each unique value appears in a column.
# print(df.shape)  # df.shape   → attribute (a stored value, like a variable)

# Resampling - e.g --> "Group all hours belonging to July 1st together, then calculate min/max."
# setting index means "Stop using 0,1,2,3 as row identifier. Use timestamp instead.
df = df.set_index("timestamp")

df_filtered = df[df.index.month.isin([7, 8])]
# print(df_filtered.index.month.unique())
# print(len(df_filtered))

daily_temp_summary = df_filtered["temperature_c"].resample("D").agg("min")
print(daily_temp_summary.isnull().sum())

daily_temp_summary = daily_temp_summary.dropna()
# print(daily_temp_summary)

daily_wind_summary = df_filtered["wind_speed_kmh"].resample("D").agg("max")
print(daily_wind_summary.isnull().sum())

daily_wind_summary = daily_wind_summary.dropna()
# print(daily_wind_summary)

# pandas combine two series into dataframe

df = pd.concat([daily_temp_summary, daily_wind_summary], axis=1)

# Deriving "Climbable" column
df["climbable"] = np.where(
    (df["temperature_c"] < -20) | (df["wind_speed_kmh"] > 40), 0, 1
)

# print(df)
# print(df["climbable"].value_counts())

# save dataframe to csv
# index=False → timestamp saved as regular column
# index=True  → timestamp saved as unnamed extra column
# ,timestamp,temperature_c,wind_speed_kmh,climbable
# 0,2021-07-01,...
df.reset_index(inplace=True)
df.to_csv("E:/Portfolio_Project/elbrus_daily_weather_2021_2022.csv", index=False)

df_check = pd.read_csv("E:/Portfolio_Project/elbrus_daily_weather_2021_2022.csv")

print(df_check.head())
print(df_check.shape)
print(df_check.columns)
