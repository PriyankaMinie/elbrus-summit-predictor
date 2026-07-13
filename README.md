# 🏔️ Elbrus Summit Predictor

An end-to-end data engineering and machine learning pipeline that predicts whether Mount Elbrus (5,642m) is safe to summit on any given day, using real weather data at summit altitude.

---

## 🔗 Live Demo (V2 — Cloud Deployment)

- **Dashboard:** [elbrus-summit-predictor.streamlit.app](https://elbrus-summit-predictor.streamlit.app)
- **API docs:** [elbrus-api.onrender.com/docs](https://elbrus-api.onrender.com/docs)

> Free-tier hosting — the API may take 30-60 seconds to wake up if it's been idle.

---

## 🎯 Project Overview

Mount Elbrus is the highest peak in Europe and one of the Seven Summits. Summit attempts are highly weather-dependent — wind, temperature, precipitation, and snowfall can turn a safe climb into a life-threatening situation within hours.

This project builds a complete data pipeline that:
- Ingests historical ERA5 weather data at 500 hPa pressure level (~5,750m altitude)
- Streams real-time Open-Meteo weather data daily
- Engineers features and trains an XGBoost classification model
- Serves predictions via a FastAPI REST endpoint
- Displays live GO/NO GO decisions on a Streamlit dashboard

The project was built in two stages: **V1**, a local proof-of-concept pipeline, and **V2**, which takes the same pipeline and deploys it to the cloud so it runs 24/7. Both are documented below.

---

## 🏗️ Architecture (V1 — Local)

```
ERA5 Historical Data (.nc)
        ↓
Python (cleaning, feature engineering)
        ↓
PostgreSQL (era5_cleaned table)
        ↓
Feature Engineering (wind_chill, lag features)
        ↓
PostgreSQL (features_daily table)
        ↓
XGBoost Model Training → elbrus_model.pkl
        ↓
FastAPI (prediction endpoint)
        ↓
Streamlit Dashboard (live GO/NO GO)
        ↑
Open-Meteo API → Kafka → Airflow → PostgreSQL (openmeteo_raw)
```

---

## ☁️ Architecture (V2 — Cloud)

V2 takes the same pipeline from V1 and moves it to the cloud, so it runs continuously without a laptop.

```
ERA5 Historical Data (.nc)
        ↓
Python (cleaning, feature engineering)
        ↓
Supabase PostgreSQL (era5_cleaned table)
        ↓
Feature Engineering (wind_chill, lag features)
        ↓
Supabase PostgreSQL (features_daily table)
        ↓
XGBoost Model Training → elbrus_model.pkl
        ↓
FastAPI on Render (prediction endpoint)
        ↓
Streamlit Community Cloud Dashboard (live GO/NO GO)
        ↑
Open-Meteo API → GitHub Actions (daily cron) → Supabase PostgreSQL (openmeteo_raw)
```

| V1 (local) | V2 (cloud) |
|---|---|
| Local PostgreSQL | Supabase (managed PostgreSQL) |
| FastAPI on `localhost:8000` | FastAPI on Render |
| Streamlit on `localhost:8501` | Streamlit Community Cloud |
| Airflow DAG (local, laptop must be on) | GitHub Actions (scheduled, serverless) |

See `MIGRATION_NOTES.md` for the full technical breakdown of what changed and why.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Data ingestion | ERA5 (ECMWF), Open-Meteo API |
| Message streaming (V1) | Apache Kafka |
| Pipeline orchestration (V1) | Apache Airflow |
| Scheduled fetch (V2) | GitHub Actions |
| Database (V1) | Local PostgreSQL |
| Database (V2) | Supabase (managed PostgreSQL) |
| Data processing | Python, Pandas, NumPy, NetCDF4 |
| ML model | XGBoost, scikit-learn |
| API serving (V1) | FastAPI, Uvicorn — local |
| API serving (V2) | FastAPI, Uvicorn — deployed on Render |
| Dashboard (V1) | Streamlit, Plotly — local |
| Dashboard (V2) | Streamlit, Plotly — deployed on Streamlit Community Cloud |
| Environment (V1) | WSL2 (Ubuntu), Windows |

---

## 📊 Model Performance

| Metric | Logistic Regression | XGBoost |
|--------|-------------------|---------|
| Accuracy | 92.7% | 98.3% |
| Precision | 84.0% | 100% |
| Recall | 93.8% | 94.3% |
| F1 | 88.0% | 96.7% |
| ROC-AUC | 98.2% | 99.5% |

**Model selected:** XGBoost — chosen for 100% precision (never gives a false GO on a dangerous day), which is critical for a safety application.

**Evaluation method:** 5-fold stratified cross-validation (chosen over single train/test split due to small dataset size of 123 rows).

---

## ⚠️ Safety Thresholds

The model was trained on these climbability rules:

| Condition | Threshold | Risk |
|-----------|-----------|------|
| Wind speed | > 40 km/h | Physical danger — cannot stand at summit |
| Precipitation | > 1 mm | Avalanche and ice formation risk |
| Snowfall | > 0.5 cm | Track loss and zero visibility |
| Temperature | < -20°C | Frostbite risk within minutes |

---

## 📁 Project Structure

```
Portfolio_Project/
├── era5_raw.nc                              # Raw ERA5 pressure level data
├── era5_precipitation_raw.nc                # Raw ERA5 single level data
├── elbrus_daily_weather_2021_2022.csv       # Cleaned ERA5 temp/wind data
├── elbrus_daily_weather_full_2021_2022.csv  # Full ERA5 with precipitation
├── explore_data.py                          # ERA5 exploration and cleaning
├── explore_era5_precipitation_data.py       # Precipitation data processing
├── build_features.py                        # Feature engineering exploration
├── load_era5.py                             # Load ERA5 to PostgreSQL
├── load_era5_full.py                        # Load full ERA5 to PostgreSQL
├── load_features_daily.py                   # Build features_daily table
├── train_model.py                           # Model training and evaluation
├── elbrus_model.pkl                         # Saved XGBoost model
├── app.py                                   # FastAPI prediction endpoint
├── dashboard.py                             # Streamlit dashboard
├── checkmeteo.py                            # Open-Meteo API testing
├── elbrus_bg.jpg                            # Dashboard background image
├── fetch_openmeteo_daily.py                 # V2: standalone fetch script for GitHub Actions
├── requirements.txt                         # V2: Streamlit Cloud dependencies
├── requirements-api.txt                     # V2: Render (FastAPI) dependencies
├── requirements-dashboard.txt                # V2: dashboard dependencies (mirrors requirements.txt)
├── MIGRATION_NOTES.md                       # V2: local-to-cloud migration details
├── .github/
│   └── workflows/
│       └── daily_openmeteo_fetch.yaml       # V2: GitHub Actions daily fetch schedule
└── dags/
    └── openmeteo_pipeline.py                # V1: Airflow DAG (local)
```

---

## 🚀 How to Run Locally (V1)

### Prerequisites
- Python 3.10+
- PostgreSQL 16
- Java 17
- WSL2 (Ubuntu)
- Apache Kafka 3.9.0

### Installation

```bash
pip install psycopg2-binary xgboost scikit-learn fastapi uvicorn streamlit plotly pandas numpy netCDF4 requests joblib apache-airflow
```

### Start all services (in order)

**Terminal 1 — Zookeeper:**
```bash
C:\kafka\bin\windows\zookeeper-server-start.bat C:\kafka\config\zookeeper.properties
```

**Terminal 2 — Kafka:**
```bash
C:\kafka\bin\windows\kafka-server-start.bat C:\kafka\config\server.properties
```

**Terminal 3 — Airflow API server (WSL):**
```bash
source ~/elbrus_env/bin/activate
airflow api-server --port 8080
```

**Terminal 4 — Airflow Scheduler (WSL):**
```bash
source ~/elbrus_env/bin/activate
airflow scheduler
```

**Terminal 5 — Airflow DAG Processor (WSL):**
```bash
source ~/elbrus_env/bin/activate
airflow dag-processor
```

**Terminal 6 — FastAPI:**
```bash
python -m uvicorn app:app --reload
```

**Terminal 7 — Streamlit Dashboard:**
```bash
python -m streamlit run dashboard.py
```

### Access points
- Streamlit Dashboard: http://localhost:8501
- FastAPI Swagger UI: http://127.0.0.1:8000/docs
- Airflow UI: http://localhost:8080

---

## ☁️ Cloud Deployment (V2)

The live deployment (linked at the top of this README) runs on:

- **Database:** [Supabase](https://supabase.com) — free-tier managed PostgreSQL
- **API:** [Render](https://render.com) — free-tier web service running `app.py` via `requirements-api.txt`
- **Dashboard:** [Streamlit Community Cloud](https://share.streamlit.io) — running `dashboard.py` via `requirements.txt`
- **Daily data fetch:** GitHub Actions, scheduled via `.github/workflows/daily_openmeteo_fetch.yaml`, replacing the local Airflow DAG for cloud runs

Credentials are stored as GitHub Secrets (for the Actions workflow) and as platform-specific environment variables/secrets on Render and Streamlit Cloud — never committed to the repo. See `MIGRATION_NOTES.md` for full details on how each service was set up and issues encountered along the way.

---

## 🔌 FastAPI Endpoint

**POST** `/predict/summit`

Request body:
```json
{
  "temperature_c": -12.5,
  "wind_speed_kmh": 28.0,
  "precipitation_mm": 0.2,
  "snowfall_cm": 0.0,
  "wind_chill": -18.3,
  "wind_lag_1": 32.0,
  "temp_lag_1": -11.0
}
```

Response:
```json
{
  "is_climbable": 1,
  "probability": 0.97,
  "recommendation": "Conditions are favourable - GO"
}
```

Try it live at the [API docs link](https://elbrus-api.onrender.com/docs) above, or locally at `127.0.0.1:8000/docs` when running V1.

---

## ⚠️ Known Limitations

### 1. Small training dataset
The model was trained on only 123 days (July-August, 2021-2022). This is a proof-of-concept — a production system would require significantly more historical data.

### 2. Temperature feature not predictive
Feature importance analysis revealed the model only uses wind speed (58.2%) and precipitation (41.8%). Temperature contributes 0% because July-August temperatures at 500 hPa never dropped below the -20°C threshold in the training data. This means the model will not correctly identify extremely cold days as dangerous.

### 3. Free-tier hosting constraints (V2)
The API (Render) and dashboard (Streamlit Cloud) run on free tiers. The API may spin down after inactivity, causing a 30-60 second delay on the first request after idle.

### 4. Summit season only
Training data covers July-August only. Shoulder season conditions (September-October) are not represented.

---

## 🔮 Future Enhancements

- [ ] Expand ERA5 dataset — download 2018-2024, include September-October
- [ ] Reconsider temperature threshold — -10°C or -12°C more realistic for summer
- [ ] Hybrid OR/AND logic for climbable label
- [ ] Retrain model with expanded dataset
- [ ] Mobile app (React Native / Flutter) using the same FastAPI backend
- [ ] Databricks integration for distributed data processing
- [ ] Mobile-responsive dashboard
- [ ] Email/SMS alerts for good summit windows

---

## 📌 Data Sources

- **ERA5:** ECMWF Reanalysis v5 — https://cds.climate.copernicus.eu
- **Open-Meteo:** Free weather API — https://open-meteo.com

---

## 👤 Author

**Priyanka** - Senior Data Engineer and mountaineer.

I wanted to build something that combines my two highest states of flow - data engineering and mountaineering. I summitted Elbrus (5,642m) and stood at the highest point in Europe in Aug, 2025. This project was born from a simple question I asked myself on the way down: what does the data actually say about summit day?

This is my answer.
