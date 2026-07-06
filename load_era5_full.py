import psycopg2
import csv
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cursor = conn.cursor()

with open("elbrus_daily_weather_full_2021_2022.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cursor.execute(
            """
            INSERT INTO era5_cleaned (timestamp, latitude, longitude, temperature_c, wind_speed_kmh, precipitation_mm, snowfall_cm, climbable)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                row["timestamp"],
                43.25,
                42.25,
                float(row["temperature_c"]),
                float(row["wind_speed_kmh"]),
                float(row["precipitation_mm"]),
                float(row["snowfall_cm"]),
                int(row["climbable"]),
            ),
        )

conn.commit()
cursor.close()
conn.close()
print("ERA5 full data loaded successfully")
