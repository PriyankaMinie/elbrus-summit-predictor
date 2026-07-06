# 🏔️ Elbrus Summit Predictor

An end-to-end data engineering and machine learning pipeline that predicts whether Mount Elbrus (5,642m) is safe to summit on any given day, using real weather data at summit altitude.

---

## 🎯 Project Overview

Mount Elbrus is the highest peak in Europe and one of the Seven Summits. Summit attempts are highly weather-dependent — wind, temperature, precipitation, and snowfall can turn a safe climb into a life-threatening situation within hours.

This project builds a complete data pipeline that:
- Ingests historical ERA5 weather data at 500 hPa pressure level (~5,750m altitude)
- Streams real-time Open-Meteo weather data daily via Apache Kafka and Airflow
- Engineers features and trains an XGBoost classification model
- Serves predictions via a FastAPI REST endpoint
- Displays live GO/NO GO decisions on a Streamlit dashboard

---

## 🏗️ Architecture

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

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Data ingestion | ERA5 (ECMWF), Open-Meteo API |
| Message streaming | Apache Kafka |
| Pipeline orchestration | Apache Airflow |
| Database | PostgreSQL |
| Data processing | Python, Pandas, NumPy, NetCDF4 |
| ML model | XGBoost, scikit-learn |
| API serving | FastAPI, Uvicorn |
| Dashboard | Streamlit, Plotly |
| Environment | WSL2 (Ubuntu), Windows |

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
└── dags/
    └── openmeteo_pipeline.py                # Airflow DAG
```

---

## 🚀 How to Run Locally

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

---

## ⚠️ Known Limitations

### 1. Small training dataset
The model was trained on only 123 days (July-August, 2021-2022). This is a proof-of-concept — a production system would require significantly more historical data.

### 2. Temperature feature not predictive
Feature importance analysis revealed the model only uses wind speed (58.2%) and precipitation (41.8%). Temperature contributes 0% because July-August temperatures at 500 hPa never dropped below the -20°C threshold in the training data. This means the model will not correctly identify extremely cold days as dangerous.

### 3. Local deployment only
All services run locally — the pipeline stops when the laptop is off. Cloud deployment is planned as a future enhancement.

### 4. Summit season only
Training data covers July-August only. Shoulder season conditions (September-October) are not represented.

---

## 🔮 Future Enhancements

- [ ] Expand ERA5 dataset — download 2018-2024, include September-October
- [ ] Reconsider temperature threshold — -10°C or -12°C more realistic for summer
- [ ] Hybrid OR/AND logic for climbable label
- [ ] Retrain model with expanded dataset
- [ ] Cloud deployment (AWS/GCP) for 24/7 pipeline operation
- [ ] Databricks integration for distributed data processing
- [ ] Mobile-responsive dashboard
- [ ] Email/SMS alerts for good summit windows

---

## 📌 Data Sources

- **ERA5:** ECMWF Reanalysis v5 — https://cds.climate.copernicus.eu
- **Open-Meteo:** Free weather API — https://open-meteo.com

---

## 👤 Author

Built by Priyanka - Senior Data Engineer and mountaineer who summitted Elbrus in Aug, 2025. This project was born from a simple question: what does the data say about summit day?
