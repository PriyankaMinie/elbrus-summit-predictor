from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import os
from dotenv import load_dotenv

default_args = {"owner": "elbrus", "retries": 1, "retry_delay": timedelta(minutes=5)}


def fetch_openmeteo(ti):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 43.25,
        "longitude": 42.25,
        "hourly": "temperature_500hPa,windspeed_500hPa,precipitation,snowfall",
        "forecast_days": 1,
    }
    response = requests.get(url, params=params)
    data = response.json()
    ti.xcom_push(key="weather_data", value=data)
    print("Fetched Open-Meteo data successfully")


def store_to_postgres(ti):
    data = ti.xcom_pull(key="weather_data", task_ids="fetch_openmeteo")
    hourly = data["hourly"]

    load_dotenv()

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


with DAG(
    dag_id="openmeteo_pipeline",
    default_args=default_args,
    description="Fetch Open-Meteo 500hPa data with precipitation for Elbrus",
    schedule="0 15 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_openmeteo", python_callable=fetch_openmeteo
    )

    store_task = PythonOperator(
        task_id="store_to_postgres", python_callable=store_to_postgres
    )

    fetch_task >> store_task
