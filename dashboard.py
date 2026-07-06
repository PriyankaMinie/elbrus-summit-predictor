import streamlit as st
import requests
import pandas as pd
import psycopg2
from datetime import datetime, date
import numpy as np
import base64
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# --- PAGE CONFIG ---
st.set_page_config(page_title="Elbrus Summit Predictor", page_icon="🏔️", layout="wide")


# --- BACKGROUND IMAGE ---
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


bg_image = get_base64_image("elbrus_bg.jpg")

st.markdown(
    f"""
<style>
.stApp {{
    background-image: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url("data:image/jpg;base64,{bg_image}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
section[data-testid="stSidebar"] {{
    background-color: rgba(0, 0, 0, 0.80);
}}
section[data-testid="stSidebar"] * {{
    color: white !important;
}}
.main .block-container {{
    background-color: rgba(0, 0, 0, 0.55);
    border-radius: 15px;
    padding: 2rem;
    backdrop-filter: blur(5px);
}}
h1, h2, h3, p, div, span, label {{
    color: white !important;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
}}
[data-testid="stMetricValue"] {{
    font-size: 2rem !important;
    font-weight: bold !important;
    color: white !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
}}
[data-testid="stMetricLabel"] {{
    font-size: 1rem !important;
    color: #DDDDDD !important;
}}
.stSubheader {{
    background-color: rgba(255, 255, 255, 0.08);
    border-left: 4px solid #FF6B00;
    padding-left: 10px;
    border-radius: 5px;
}}
div[data-testid="stAlertContentError"] {{
    background-color: rgba(180, 0, 0, 0.90) !important;
    border: 2px solid #FF0000 !important;
    border-radius: 10px !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}}
div[data-testid="stAlertContentSuccess"] {{
    background-color: rgba(0, 100, 0, 0.85) !important;
    border: 2px solid #00CC44 !important;
    border-radius: 10px !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}}
div[data-testid="stAlertContentInfo"] {{
    background-color: rgba(0, 50, 150, 0.85) !important;
    border: 2px solid #4499FF !important;
    border-radius: 10px !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}}
div[data-testid="stAlertContentWarning"] {{
    background-color: rgba(150, 100, 0, 0.85) !important;
    border: 2px solid #FFA500 !important;
    border-radius: 10px !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR ---
with st.sidebar:
    st.image("elbrus_bg.jpg", use_container_width=True)
    st.title(" About")
    st.write("**Mount Elbrus**")
    st.write("• Elevation: 5,642m")
    st.write("• Location: Caucasus, Russia")
    st.write("• Highest peak in Europe")
    st.divider()
    st.write("**Model Information**")
    st.write("• Algorithm: XGBoost")
    st.write("• Training data: 123 days")
    st.write("• Features: 7")
    st.write("• Accuracy: 98.3%")
    st.write("• Precision: 100%")
    st.write("• Recall: 94.3%")
    st.divider()
    st.write("**Safety Thresholds**")
    st.write("• Wind > 40 km/h → NO GO")
    st.write("• Precipitation > 1mm → NO GO")
    st.write("• Snowfall > 0.5cm → NO GO")
    st.write("• Temperature < -20°C → NO GO")
    st.divider()
    st.caption(
        "⚠️ This tool is for informational purposes only. Always consult a certified mountain guide."
    )

# --- HEADER ---
st.title("Elbrus Summit Predictor")
st.caption(
    f"Mount Elbrus, Russia (43.25°N, 42.25°E) | {date.today().strftime('%B %d, %Y')} | Data at 500 hPa (~5750m)"
)
st.divider()


# --- FETCH WEATHER ---
@st.cache_data(ttl=3600)
def fetch_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 43.25,
        "longitude": 42.25,
        "hourly": "temperature_500hPa,windspeed_500hPa,precipitation,snowfall",
        "forecast_days": 7,
    }
    response = requests.get(url, params=params)
    return response.json()


data = fetch_weather()
hourly = data["hourly"]

df = pd.DataFrame(
    {
        "timestamp": pd.to_datetime(hourly["time"]),
        "temperature_c": hourly["temperature_500hPa"],
        "wind_speed_kmh": hourly["windspeed_500hPa"],
        "precipitation_mm": hourly["precipitation"],
        "snowfall_cm": hourly["snowfall"],
    }
)

today = df[df["timestamp"].dt.date == date.today()]
temp_today = today["temperature_c"].min()
wind_today = today["wind_speed_kmh"].max()
precip_today = today["precipitation_mm"].max()
snow_today = today["snowfall_cm"].max()

# --- CURRENT CONDITIONS ---
st.subheader("Current Conditions at Summit Altitude (500 hPa)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Min Temperature", f"{temp_today:.1f}°C")
col2.metric("💨 Max Wind", f"{wind_today:.1f} km/h")
col3.metric("🌧️ Max Precipitation", f"{precip_today:.2f} mm")
col4.metric("❄️ Max Snowfall", f"{snow_today:.2f} cm")

st.divider()

# --- SUMMIT PREDICTION ---
st.subheader("Summit Prediction")

wind_chill_today = (
    13.12
    + 0.6215 * temp_today
    - 11.37 * (wind_today**0.16)
    + 0.3965 * temp_today * (wind_today**0.16)
)

yesterday = df[df["timestamp"].dt.date == (date.today() - pd.Timedelta(days=1))]
wind_lag = yesterday["wind_speed_kmh"].max() if len(yesterday) > 0 else wind_today
temp_lag = yesterday["temperature_c"].min() if len(yesterday) > 0 else temp_today

payload = {
    "temperature_c": round(float(temp_today), 2),
    "wind_speed_kmh": round(float(wind_today), 2),
    "precipitation_mm": round(float(precip_today), 2),
    "snowfall_cm": round(float(snow_today), 2),
    "wind_chill": round(float(wind_chill_today), 2),
    "wind_lag_1": round(float(wind_lag), 2),
    "temp_lag_1": round(float(temp_lag), 2),
}

try:
    response = requests.post("http://127.0.0.1:8000/predict/summit", json=payload)
    result = response.json()
    is_climbable = result["is_climbable"]
    probability = result["probability"]
    recommendation = result["recommendation"]

    col1, col2 = st.columns([2, 1])
    with col1:
        if is_climbable == 1:
            st.success(f"✅ GO — {recommendation}")
        else:
            st.error(f"❌ DO NOT GO — {recommendation}")
    with col2:
        st.metric(
            "Model Confidence",
            (
                f"{probability*100:.0f}%"
                if is_climbable == 1
                else f"{(1-probability)*100:.0f}%"
            ),
        )

except Exception as e:
    st.warning(
        "⚠️ Could not connect to prediction API. Make sure FastAPI is running on port 8000."
    )

st.divider()

# --- SAFETY ALERTS ---
st.subheader("⚠️ Safety Alerts")
alerts = []
if precip_today > 1:
    alerts.append(
        f"🌧️ Heavy precipitation: {precip_today:.2f}mm — Avalanche and ice risk"
    )
if snow_today > 0.5:
    alerts.append(f"❄️ Snowfall: {snow_today:.2f}cm — Track loss and visibility risk")
if wind_today > 40:
    alerts.append(f"💨 High wind: {wind_today:.1f}km/h — Physical danger at summit")
if temp_today < -20:
    alerts.append(
        f"🌡️ Extreme cold: {temp_today:.1f}°C — Frostbite risk within minutes"
    )

if alerts:
    for alert in alerts:
        st.error(alert)
else:
    st.success("✅ No critical safety alerts for today")

st.divider()

# --- 7-DAY FORECAST BAR CHART ---
st.subheader("7-Day Summit Forecast")

df["date"] = df["timestamp"].dt.date
daily = (
    df.groupby("date")
    .agg(
        temperature_c=("temperature_c", "min"),
        wind_speed_kmh=("wind_speed_kmh", "max"),
        precipitation_mm=("precipitation_mm", "max"),
        snowfall_cm=("snowfall_cm", "max"),
    )
    .reset_index()
)

daily["climbable"] = (
    (daily["wind_speed_kmh"] <= 40)
    & (daily["precipitation_mm"] <= 1)
    & (daily["snowfall_cm"] <= 0.5)
).astype(int)

daily["status"] = daily["climbable"].map({1: "✅ GO", 0: "❌ NO GO"})
daily["color"] = daily["climbable"].map({1: "#00CC44", 0: "#FF0000"})
daily["date_str"] = daily["date"].astype(str)

fig_forecast = go.Figure()
fig_forecast.add_trace(
    go.Bar(
        x=daily["date_str"],
        y=daily["wind_speed_kmh"],
        marker_color=daily["color"],
        text=daily["status"],
        textposition="outside",
        name="Max Wind (km/h)",
    )
)
fig_forecast.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0.3)",
    font_color="white",
    font=dict(size=13, color="white"),
    xaxis=dict(
        tickfont=dict(size=13, color="white"),
        title_font=dict(size=14, color="white"),
        gridcolor="rgba(255,255,255,0.2)",
    ),
    yaxis=dict(
        tickfont=dict(size=13, color="white"),
        title_font=dict(size=14, color="white"),
        gridcolor="rgba(255,255,255,0.2)",
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0.7)",
        bordercolor="white",
        borderwidth=1,
        font=dict(size=13, color="white"),
    ),
)
fig_forecast.add_hline(
    y=40,
    line_dash="dash",
    line_color="red",
    annotation_text="40 km/h safety threshold",
    annotation_position="top right",
)
st.plotly_chart(fig_forecast, use_container_width=True)

st.divider()

# --- HISTORICAL DATA ---
st.subheader("Historical Summit Patterns (2021-2022)")

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

df_hist = pd.read_sql(
    """
    SELECT timestamp, temperature_c, wind_speed_kmh, climbable 
    FROM era5_cleaned 
    ORDER BY timestamp
""",
    conn,
)
conn.close()

df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
df_hist["status"] = df_hist["climbable"].map({1: "Climbable", 0: "Not Climbable"})
df_hist["color"] = df_hist["climbable"].map({1: "#00CC44", 0: "#CC2200"})

col1, col2 = st.columns(2)

with col1:
    fig_temp = px.scatter(
        df_hist,
        x="timestamp",
        y="temperature_c",
        color="status",
        color_discrete_map={"Climbable": "#00CC44", "Not Climbable": "#FF0000"},
        title="Temperature History — Climbable vs Not Climbable",
        labels={"temperature_c": "Temperature (°C)", "timestamp": "Date"},
    )
    fig_temp.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.3)",
        font_color="white",
        font=dict(size=13, color="white"),
        xaxis=dict(
            tickfont=dict(size=13, color="white"),
            title_font=dict(size=14, color="white"),
            gridcolor="rgba(255,255,255,0.2)",
        ),
        yaxis=dict(
            tickfont=dict(size=13, color="white"),
            title_font=dict(size=14, color="white"),
            gridcolor="rgba(255,255,255,0.2)",
        ),
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with col2:
    fig_wind = px.scatter(
        df_hist,
        x="timestamp",
        y="wind_speed_kmh",
        color="status",
        color_discrete_map={"Climbable": "#00CC44", "Not Climbable": "#FF0000"},
        title="Wind Speed History — Climbable vs Not Climbable",
        labels={"wind_speed_kmh": "Wind Speed (km/h)", "timestamp": "Date"},
    )
    fig_wind.add_hline(
        y=40, line_dash="dash", line_color="red", annotation_text="40 km/h threshold"
    )
    fig_wind.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.3)",
        font_color="white",
        font=dict(size=13, color="white"),
        xaxis=dict(
            tickfont=dict(size=13, color="white"),
            title_font=dict(size=14, color="white"),
            gridcolor="rgba(255,255,255,0.2)",
        ),
        yaxis=dict(
            tickfont=dict(size=13, color="white"),
            title_font=dict(size=14, color="white"),
            gridcolor="rgba(255,255,255,0.2)",
        ),
    )
    st.plotly_chart(fig_wind, use_container_width=True)

climbable_days = df_hist["climbable"].sum()
total_days = len(df_hist)
st.success(
    f"📈 Out of {total_days} historical days — {climbable_days} were climbable ({climbable_days/total_days*100:.1f}%)"
)
