import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def fetch_openmeteo():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 43.25,
        "longitude": 42.25,
        "hourly": "temperature_500hPa,windspeed_500hPa,precipitation,snowfall",
        "forecast_days": 1,
    }
    response = requests.get(url, params=params)
    data = response.json()
    print("Fetched Open-Meteo data successfully")
    return data


def store_to_postgres(data):
    hourly = data["hourly"]
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cursor = conn.cursor()
    for i in range(len(hourly["time"])):
        cursor.execute(
            """
            INSERT INTO openmeteo_raw (timestamp, latitude, longitude, temperature_c, wind_speed_kmh, precipitation_mm, snowfall_cm)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (timestamp) DO NOTHING
            """,
            (
                hourly["time"][i],
                43.25,
                42.25,
                hourly["temperature_500hPa"][i],
                hourly["windspeed_500hPa"][i],
                hourly["precipitation"][i],
                hourly["snowfall"][i],
            ),
        )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(hourly['time'])} rows into openmeteo_raw")


if __name__ == "__main__":
    weather_data = fetch_openmeteo()
    store_to_postgres(weather_data)