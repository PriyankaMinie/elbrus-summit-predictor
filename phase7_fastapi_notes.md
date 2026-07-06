# Phase 7 — FastAPI Prediction Endpoint: Complete Summary

---

## 1. What FastAPI Does in This Project

FastAPI wraps the trained XGBoost model (`elbrus_model.pkl`) in a web endpoint. Any client — Streamlit dashboard, mobile app, guide's phone — can send today's weather data and get back a summit prediction without needing to know anything about Python or XGBoost.

**Simple analogy:**

- FastAPI = the kitchen (processes orders, returns results, never seen by the user)
- Streamlit = the dining room (the visual interface the user actually interacts with)
- HTTP request = the waiter passing orders between them

---

## 2. Installation

```
pip install fastapi uvicorn
```

- `fastapi` — the web framework
- `uvicorn` — the ASGI server that runs the FastAPI application

---

## 3. How to Start the Server

```
python -m uvicorn app:app --reload
```

- `app:app` — first `app` is the filename (`app.py`), second `app` is the FastAPI instance inside it
- `--reload` — auto-restarts the server whenever you save changes to `app.py` (development mode only)

**Server runs at:** `http://127.0.0.1:8000`

---

## 4. Key URLs

| URL                                    | Purpose                                     |
| -------------------------------------- | ------------------------------------------- |
| `http://127.0.0.1:8000/`               | Home endpoint — health check                |
| `http://127.0.0.1:8000/docs`           | Swagger UI — interactive API documentation  |
| `http://127.0.0.1:8000/openapi.json`   | Raw OpenAPI JSON spec that Swagger UI reads |
| `http://127.0.0.1:8000/predict/summit` | Prediction endpoint (POST)                  |

--

## 6. Code Explained — Line by Line

### Imports

```python
from fastapi import FastAPI        # main framework
from pydantic import BaseModel     # input validation
import joblib                      # load saved model
import numpy as np                 # array format for XGBoost
```

### App instance

```python
app = FastAPI()
```

Creates the FastAPI application. Everything attaches to this object.

### Model loading

```python
model = joblib.load("elbrus_model.pkl")
```

Loads the trained XGBoost model once at server startup — not on every request. Critical for performance.

### Input schema (Pydantic)

```python
class WeatherInput(BaseModel):
    temperature_c: float
    ...
```

Defines and validates the 7 required input fields. If any field is missing or wrong type, FastAPI automatically returns a `422 Unprocessable Entity` error with a clear message — before the model even runs.

### Home endpoint

```python
@app.get("/")
def home():
    return {"message": "..."}
```

`@app.get("/")` is a decorator — it tells FastAPI "run this function when a GET request arrives at /". Returns a simple JSON health check message.

### Prediction endpoint

```python
@app.post("/predict/summit")
def predict_summit(data: WeatherInput):
```

`@app.post` — POST method because we're sending data in the request body.
`data: WeatherInput` — FastAPI reads the JSON body, validates it, and passes it as `data`.

### Feature array

```python
features = np.array([[...]])
```

Converts input to a 2D NumPy array with shape `(1, 7)` — 1 sample, 7 features. Order must match training order exactly.

### Prediction

```python
prediction = model.predict(features)[0]         # 0 or 1
probability = model.predict_proba(features)[0][1]  # probability of class 1 (climbable)
```

`predict()` → binary label
`predict_proba()` → array of `[prob_of_0, prob_of_1]`; `[0][1]` gets climbable probability

### Response

```python
return {
    "is_climbable": int(prediction),
    "probability": round(float(probability), 2),
    "recommendation": recommendation
}
```

`int()` and `float()` — converts NumPy types to standard Python types for JSON serialization.

---

## 7. What is Swagger UI?

Swagger UI is an open-source tool that generates an interactive visual documentation page for any API following the OpenAPI standard.

**Connection between FastAPI and Swagger UI:**

```
FastAPI code → auto-generates openapi.json → Swagger UI reads it → renders /docs page
```

FastAPI has Swagger UI built in by default — no configuration needed. Every endpoint you write automatically appears at `/docs` with a **Try it out** button for live testing.

**What Swagger UI shows for each endpoint:**

- HTTP method and URL
- All input fields and their types
- Live testing form
- Response format and status codes

---

## 8. HTTP Methods — GET vs POST

| Method | Used for     | Has request body? |
| ------ | ------------ | ----------------- |
| GET    | Reading data | No                |
| POST   | Sending data | Yes               |

Home endpoint uses GET (no data needed, just checking if API is alive).
Prediction endpoint uses POST (must send weather data in the request body).

---

## 9. Test Cases

### GO scenario (safe day):

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

**Response:** `is_climbable: 1, probability: 0.97, "Conditions are favourable - GO"`

### NO GO scenario (dangerous day):

```json
{
  "temperature_c": -13.0,
  "wind_speed_kmh": 65.0,
  "precipitation_mm": 2.5,
  "snowfall_cm": 0.0,
  "wind_chill": -28.0,
  "wind_lag_1": 55.0,
  "temp_lag_1": -12.0
}
```

**Response:** `is_climbable: 0, probability: 0.01, "Conditions are dangerous - DO NOT GO"`

---

## 10. Known Limitation — Temperature Ignored

When tested with `temperature_c: -31` (below -20°C threshold) but low wind and zero precipitation, the model **still returned GO**.

**Why:** Feature importance showed temperature contributes 0% to predictions because July-August ERA5 training data never had temperatures below -20°C — the threshold was never triggered during training. The model correctly learned temperature is irrelevant for this specific dataset, but this makes it dangerously wrong for extreme cold scenarios.

**Fix:** Retrain with expanded dataset including shoulder seasons (September-October) where temperatures drop below -20°C. See Phase 6 notes for full details.

---

## 11. Production Note

FastAPI runs locally at `http://127.0.0.1:8000` — only accessible on my machine. In production, this would be deployed on a cloud server (AWS EC2, GCP Cloud Run, etc.) with a public URL so the Streamlit dashboard and other clients can reach it from anywhere.
