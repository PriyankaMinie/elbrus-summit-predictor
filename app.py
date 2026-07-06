# from fastapi import FastAPI
# import joblib
# import numpy as np

# app = FastAPI()

# model = joblib.load("elbrus_model.pkl")


# @app.get("/")
# def home():
#     return {"message": "elbrus summit predictor is running"}

from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI()

model = joblib.load("elbrus_model.pkl")


class WeatherInput(BaseModel):
    temperature_c: float
    wind_speed_kmh: float
    precipitation_mm: float
    snowfall_cm: float
    wind_chill: float
    wind_lag_1: float
    temp_lag_1: float


@app.get("/")
def home():
    return {"message": "Elbrus Summit Predictor API is running"}


@app.post("/predict/summit")
def predict_summit(data: WeatherInput):
    features = np.array(
        [
            [
                data.temperature_c,
                data.wind_speed_kmh,
                data.precipitation_mm,
                data.snowfall_cm,
                data.wind_chill,
                data.wind_lag_1,
                data.temp_lag_1,
            ]
        ]
    )

    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1]

    recommendation = (
        "Conditions are favourable - GO"
        if prediction == 1
        else "Conditions are dangerous - DO NOT GO"
    )

    return {
        "is_climbable": int(prediction),
        "probability": round(float(probability), 2),
        "recommendation": recommendation,
    }
