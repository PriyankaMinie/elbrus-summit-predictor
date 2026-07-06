import requests

# Test 1 - surface level (original)
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 43.25,
    "longitude": 42.25,
    "hourly": "temperature_2m,wind_speed_10m,visibility",
    "forecast_days": 1,
}
response = requests.get(url, params=params)
data = response.json()
print("=== SURFACE LEVEL ===")
print("Elevation:", data.get("elevation"))
print("Sample temp:", data["hourly"]["temperature_2m"][0])
print("Sample wind:", data["hourly"]["wind_speed_10m"][0])

# Test 2 - pressure level (summit altitude check)
params2 = {
    "latitude": 43.25,
    "longitude": 42.25,
    "hourly": "temperature_500hPa,windspeed_500hPa,geopotential_height_500hPa",
    "forecast_days": 1,
}
response2 = requests.get(url, params=params2)
data2 = response2.json()
print("\n=== PRESSURE LEVEL 500hPa (summit altitude) ===")
print("Full response:", data2)

# Test 3 - check visibility at 500hPa
params3 = {
    "latitude": 43.25,
    "longitude": 42.25,
    "hourly": "temperature_500hPa,windspeed_500hPa,visibility",
    "forecast_days": 1,
}
response3 = requests.get(url, params=params3)
data3 = response3.json()
print("\n=== 500hPa + VISIBILITY ===")
print("Units:", data3.get("hourly_units"))
print("Sample temp:", data3["hourly"]["temperature_500hPa"][0])
print("Sample wind:", data3["hourly"]["windspeed_500hPa"][0])
print("Sample visibility:", data3["hourly"]["visibility"][0])

# Test 4 - precipitation and snowfall
params4 = {
    "latitude": 43.25,
    "longitude": 42.25,
    "hourly": "temperature_500hPa,windspeed_500hPa,precipitation,snowfall",
    "forecast_days": 1,
}
response4 = requests.get(url, params=params4)
data4 = response4.json()
print("\n=== PRECIPITATION & SNOWFALL ===")
print("Units:", data4.get("hourly_units"))
print("Sample precipitation:", data4["hourly"]["precipitation"][0])
print("Sample snowfall:", data4["hourly"]["snowfall"][0])

params5 = {
    "latitude": 43.25,
    "longitude": 42.25,
    "hourly": "temperature_500hPa,windspeed_500hPa,precipitation,snowfall",
    "forecast_days": 1,
}
response5 = requests.get(url, params=params5)
data5 = response5.json()
print("\n=== COMBINED REQUEST ===")
print("Units:", data5.get("hourly_units"))
print("Sample temp:", data5["hourly"]["temperature_500hPa"][0])
print("Sample wind:", data5["hourly"]["windspeed_500hPa"][0])
print("Sample precip:", data5["hourly"]["precipitation"][0])
print("Sample snow:", data5["hourly"]["snowfall"][0])
