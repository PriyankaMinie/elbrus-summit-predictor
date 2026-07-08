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

with open("openmeteo_export.csv", "r") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cursor.execute(
            """
            INSERT INTO openmeteo_raw (timestamp, latitude, longitude, wind_speed_kmh, temperature_c, created_at, precipitation_mm, snowfall_cm)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (timestamp) DO NOTHING
            """,
            (
                row["timestamp"],
                float(row["latitude"]),
                float(row["longitude"]),
                float(row["wind_speed_kmh"]),
                float(row["temperature_c"]),
                row["created_at"],
                float(row["precipitation_mm"]),
                float(row["snowfall_cm"]),
            ),
        )
        count += 1

conn.commit()
cursor.close()
conn.close()
print(f"Loaded {count} rows into Supabase openmeteo_raw")
