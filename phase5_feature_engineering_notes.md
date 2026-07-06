# Phase 5 — Feature Engineering: Complete Summary

---

## What Changed Since the Original Plan

The original plan only had `temperature_c` and `wind_speed_kmh` as features. During this phase, we added **precipitation** and **snowfall** after recognizing they are critical safety factors for Elbrus summit decisions that the original plan missed.

---

## 1. The Altitude Mismatch Discovery

**Problem found:** Open-Meteo's default API returns weather at **surface level (3115m elevation)** — base camp area, not the summit (5642m). Temperatures came back positive (0.5°C to 6.7°C) which didn't match ERA5's summit-level data (-14.9°C to -5.9°C).

**Root cause:** ERA5 data was downloaded at **500 hPa pressure level** (~5750m altitude) — close to summit. Open-Meteo's default `temperature_2m` / `wind_speed_10m` variables are surface measurements.

**Fix:** Switched Open-Meteo API calls to use pressure-level variables:

```
temperature_500hPa, windspeed_500hPa
```

This matches ERA5's altitude and brought both data sources into the same range and units (°C, km/h).

**Visibility was dropped entirely** — not available at pressure level, and ERA5 never had visibility data to train on anyway.

---

## 2. Adding Precipitation and Snowfall

**Why:** Precipitation and snowfall are critical real-world summit safety factors, more important to a mountaineer than the original plan accounted for.

**ERA5 limitation discovered:** Precipitation (`tp`) and snowfall (`sf`) are **not available in the ERA5 pressure-level dataset** — they only exist in the **single-levels** dataset, always at surface level. This is a structural limitation of ERA5, not a mistake.

**Solution — two ERA5 files joined:**

- `era5_raw.nc` — pressure levels (500 hPa) → temperature, wind
- `era5_precipitation_raw.nc` — single levels (surface) → precipitation, snowfall

Both downloaded for the same period (July-August, 2021-2022) and same Elbrus coordinates, then joined on `timestamp`.

**Unit conversions applied:**

- Precipitation: metres → mm (×1000)
- Snowfall: metres of water equivalent → cm (×100)

**Aggregation rule:** Daily values use `MAX()` (worst hour of the day) — confirmed via research that climbers should plan around peak-hour risk, not daily averages.

---

## 3. Re-deriving the `climbable` Label

**Original logic (temperature + wind only):**

```python
climbable = 0 if temperature < -20 or wind > 40 else 1
```

**New logic (all 4 variables):**

```python
climbable = 0 if (
    temperature_c < -20
    or wind_speed_kmh > 40
    or precipitation_mm > 1
    or snowfall_cm > 0.5
) else 1
```

**Thresholds based on research:**

- Hurricane-force wind and sudden weather shifts are known killers on Elbrus
- Any precipitation at base level becomes snow/ice at summit altitude
- Heavy snowfall causes track loss and zero visibility

**Result:** Label distribution changed from the original — 20 days flipped from climbable to not-climbable once precipitation was factored in. New distribution: 89 not climbable, 35 climbable (out of 124 days).

**Important — snowfall almost never triggered the rule.** July-August at Elbrus has near-zero snowfall. This is expected and doesn't indicate a data problem.

---

## 4. Why Visibility and Snowfall-as-ML-feature Were Reconsidered (and partially rejected)

**Visibility:** Rejected entirely. ERA5 never had visibility to train on, and Open-Meteo's visibility is surface-level only — not representative of summit conditions. Including it would create an inconsistency the model can't learn from.

**Snowfall as a pure ML feature (without re-deriving the label):** Initially considered keeping snowfall as just a "dashboard alert" rather than an ML feature, since July-August ERA5 snowfall is nearly always zero (low predictive value in training).

**Final decision:** Snowfall WAS included as a proper ML feature, but only after redownloading ERA5 single-levels data and re-deriving `climbable` to reflect it — ensuring the label and the feature are consistent, even though its statistical impact on training is currently small.

---

## 5. Engineered Features

**Wind chill** — using the standard Environment Canada / NWS formula (valid for temps below 10°C and wind above 4.8 km/h, which always holds true for Elbrus):

```
wind_chill = 13.12 + 0.6215×T - 11.37×(V^0.16) + 0.3965×T×(V^0.16)
```

Where T = temperature_c, V = wind_speed_kmh

**Lag features** — yesterday's values, to help the model detect worsening/improving trends:

```python
wind_lag_1 = wind_speed_kmh.shift(1)
temp_lag_1 = temperature_c.shift(1)
```

**First row dropped** — July 1, 2021 has no "yesterday," so `wind_lag_1`/`temp_lag_1` are null for that row. Dropped using:

```python
df.dropna(subset=["wind_lag_1", "temp_lag_1"])
```

(Not a blind `.dropna()` — that would have wiped the entire table due to the always-null `pressure_hpa` column.)

---

## 6. Final Table Structures

### `era5_cleaned` (training source — cleaned raw measurements)

| Column              | Type      | Notes                                                 |
| ------------------- | --------- | ----------------------------------------------------- |
| id                  | SERIAL    |                                                       |
| timestamp           | TIMESTAMP |                                                       |
| latitude, longitude | FLOAT     | always 43.25, 42.25 — constant, not used in ML        |
| temperature_c       | FLOAT     | from 500hPa pressure level                            |
| wind_speed_kmh      | FLOAT     | from 500hPa pressure level                            |
| pressure_hpa        | FLOAT     | **always NULL — unused placeholder, never populated** |
| precipitation_mm    | FLOAT     | from single-levels surface data                       |
| snowfall_cm         | FLOAT     | from single-levels surface data                       |
| climbable           | INTEGER   | re-derived label using all 4 variables                |
| created_at          | TIMESTAMP | pipeline metadata only, not a feature                 |

124 rows (July-August, 2021-2022).

### `openmeteo_raw` (prediction source — live data)

Same weather columns as above (minus pressure_hpa, climbable, label) — fetched daily via Airflow DAG at 500hPa + surface precipitation/snowfall, schedule `0 15 * * *` (6 PM Elbrus time).

### `features_daily` (ML-ready training table)

| Column           | Type    |
| ---------------- | ------- |
| id               | SERIAL  |
| timestamp        | DATE    |
| temperature_c    | FLOAT   |
| wind_speed_kmh   | FLOAT   |
| precipitation_mm | FLOAT   |
| snowfall_cm      | FLOAT   |
| wind_chill       | FLOAT   |
| wind_lag_1       | FLOAT   |
| temp_lag_1       | FLOAT   |
| is_climbable     | INTEGER |

123 rows (1 dropped for missing lag data). **This is the table the XGBoost model will train on.**

---

## 7. Why Open-Meteo Data Is NOT in `features_daily`

`features_daily` is training data only — it requires a known `climbable` label. Open-Meteo represents live/future conditions where the label is unknown (that's what we're predicting).

**The correct flow going forward:**

- `era5_cleaned` → feeds `features_daily` → trains the model
- `openmeteo_raw` → aggregated fresh at request-time → fed into the trained model via FastAPI → produces a live prediction (not stored as training data)

Mixing the two would corrupt training with unlabeled or assumed data.

---

## 8. Key Scripts Created This Phase

| Script                               | Purpose                                                                                                                                |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `checkmeteo.py`                      | API exploration — tested surface vs pressure-level vs combined Open-Meteo requests                                                     |
| `explore_era5_precipitation_data.py` | Extracted, converted units, resampled, and merged precipitation/snowfall with existing ERA5 temp/wind data; re-derived climbable label |
| `load_era5_full.py`                  | Loaded the final combined ERA5 CSV (`elbrus_daily_weather_full_2021_2022.csv`) into `era5_cleaned`                                     |
| `load_features_daily.py`             | Loads `era5_cleaned`, applies wind_chill + lag feature engineering, inserts into `features_daily`                                      |

---

## 9. Outstanding Note for Later

The DAG, Kafka, Airflow, and PostgreSQL all run locally — they will NOT run automatically if the laptop is off. This is a known limitation of local development, to be addressed with a cloud deployment step after the core model and dashboard are complete.
