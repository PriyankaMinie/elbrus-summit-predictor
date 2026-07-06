# Phase 6 — Model Training: Complete Summary

---

## 1. Models Compared

Two models were evaluated and compared:

- **Logistic Regression** — simple, interpretable, good baseline for binary classification
- **XGBoost** — gradient boosted decision trees, industry standard, more complex

---

## 2. Why Cross-Validation Instead of a Single Train/Test Split

With only 123 rows, a single 80/20 split gives only ~25 test rows — too few to reliably evaluate model performance. A lucky or unlucky split could make the model look much better or worse than it actually is.

**5-Fold Stratified Cross-Validation** was used instead:

- Data split into 5 equal folds
- Each fold takes a turn as the test set while the other 4 are used for training
- Every row gets tested exactly once
- Results averaged across all 5 folds — much more reliable than a single split

**Why Stratified:** The dataset is imbalanced (89 not climbable vs 34 climbable — 72/28 split). Regular KFold splits randomly, which could accidentally put very few climbable examples in some folds. StratifiedKFold ensures every fold maintains the same 72/28 ratio, giving consistent evaluation across all folds.

---

## 3. Results — Full Metric Comparison

| Metric    | Logistic Regression | XGBoost | Winner  |
| --------- | ------------------- | ------- | ------- |
| Accuracy  | 92.7%               | 98.3%   | XGBoost |
| Precision | 84.0%               | 100%    | XGBoost |
| Recall    | 93.8%               | 94.3%   | Tie     |
| F1        | 88.0%               | 96.7%   | XGBoost |
| ROC-AUC   | 98.2%               | 99.5%   | XGBoost |

XGBoost wins on every metric. Logistic Regression's high ROC-AUC (98.2%) despite lower accuracy (92.7%) suggests it ranks days well but sometimes misplaces the decision threshold — fixable by tuning the threshold from default 0.5 to a higher value, but left as a future improvement.

### Why each metric matters for this use case:

- **Precision** — most critical. A false GO on a dangerous day is life-threatening.
- **Recall** — important. Missing genuinely safe days wastes climbing opportunities.
- **F1** — balances precision and recall. Good single summary metric for imbalanced data.
- **ROC-AUC** — measures overall class separation ability. Useful for imbalanced datasets.
- **Accuracy** — least reliable alone for imbalanced data (72/28 split). Always check alongside other metrics.

---

### 4. Why each metric matters for this use case:

- **Precision** — most critical. A false GO on a dangerous day is life-threatening.
- **Recall** — important. Missing genuinely safe days wastes climbing opportunities.
- **F1** — balances precision and recall. Good single summary metric for imbalanced data.
- **ROC-AUC** — measures overall class separation ability. Useful for imbalanced datasets.
- **Accuracy** — least reliable alone for imbalanced data (72/28 split). Always check alongside other metrics.
  Save and tell me when done.can you help me to understand the theory behind these 5 metrics in one line in my particular use case?Sure — one line each, specific to your Elbrus summit predictor:

Accuracy — "Out of all 123 days, how many did the model correctly classify as climbable or not climbable?"
Precision — "When the model says 'GO summit today', how often is it actually safe to go?" (most critical — a wrong GO could kill someone)
Recall — "Out of all the days that were genuinely safe to summit, how many did the model correctly identify as safe?" (missing safe days = wasted opportunities)
F1 — "Does the model balance catching real safe days AND not giving false green lights, or is it sacrificing one for the other?" (single score that penalizes models that are good at one but terrible at the other)
ROC-AUC — "How well can the model distinguish a climbable day from a non-climbable day overall, across all possible decision thresholds?" (above 0.98 means the model is excellent at separating the two classes, regardless of where you set the cutoff)

---

## 5. Model Selection: XGBoost

XGBoost was selected for the following reasons:

| Metric    | Logistic Regression | XGBoost | Winner  |
| --------- | ------------------- | ------- | ------- |
| Accuracy  | 92.7%               | 98.3%   | XGBoost |
| Precision | 84.0%               | 100%    | XGBoost |
| Recall    | 93.8%               | 94.3%   | Tie     |
| F1        | 88.0%               | 96.7%   | XGBoost |
| ROC-AUC   | 98.2%               | 99.5%   | XGBoost |

XGBoost wins on every metric. Logistic Regression's high ROC-AUC (98.2%) despite lower accuracy (92.7%) suggests it ranks days well but sometimes misplaces the decision threshold — fixable by tuning the threshold from default 0.5 to a higher value, but left as a future improvement.

**Known limitation:** XGBoost's near-perfect scores on a 123-row dataset are suspicious and likely indicate **overfitting** — the model may be memorizing the training data rather than learning generalizable patterns. Logistic Regression's 92.7% with more variation across folds is arguably more honest. This limitation is documented for interviews.

---

## 6. XGBoost Configuration Used

```python
XGBClassifier(
    n_estimators=50,      # fewer trees to reduce overfitting risk on small data
    max_depth=2,          # shallow trees — less complex, less memorization
    learning_rate=0.1,    # conservative learning — each tree contributes less
    random_state=42       # reproducibility
)
```

---

## 7. Feature Importance — Critical Finding

```
wind_speed_kmh      58.2%
precipitation_mm    41.8%
temperature_c        0.0%
snowfall_cm          0.0%
wind_chill           0.0%
wind_lag_1           0.0%
temp_lag_1           0.0%
```

**The model only used 2 out of 7 features.**

**Why this happened:**

The `climbable` label was derived from 4 threshold rules:

```python
climbable = 0 if (
    wind_speed_kmh > 40       ← triggered frequently
    or precipitation_mm > 1   ← triggered frequently
    or temperature_c < -20    ← NEVER triggered in data
    or snowfall_cm > 0.5      ← NEVER triggered in data
)
```

In July-August ERA5 data at 500hPa:

- Temperatures ranged from -5°C to -14°C — **never reached -20°C**
- Snowfall was essentially always zero in peak summer months

This means temperature and snowfall **never actually caused a "not climbable" label** in the training data. The model correctly identified them as useless for this dataset — because they were.

**The model essentially learned two rules:**

```
if wind > 40 → not climbable
elif precipitation > 1 → not climbable
else → climbable
```

This explains the near-perfect accuracy — it's replicating the labeling logic, not learning complex weather patterns.

---

## 8. What This Reveals — Honest Assessment

The model is not broken — it correctly learned from the data it was given. But the data itself has limitations:

- Only 123 days (July-August 2021-2022)
- Temperature threshold of -20°C is too extreme for summer months at 500hPa — never triggered in training data
- Snowfall is negligible in July-August — never triggered in training data
- Lag features and wind_chill added no value because the underlying features they're derived from weren't predictive in this dataset

---

## 9. Interview Talking Point

This is a strong portfolio talking point — not a weakness:

_"Feature importance analysis revealed the model was only using wind speed and precipitation. This led me to identify that my temperature threshold (-20°C) was outside the range of my July-August training data, where temperatures at 500hPa never dropped that low. In a production system with more historical data across all seasons and years, temperature, snowfall, wind chill, and lag features would become genuinely meaningful predictors. This is a documented limitation, not an oversight."_

---

## 10. Future Improvements (Planned)

- Download ERA5 data for more years (2018-2024 minimum)
- Include shoulder months (September, October) where:
  - Temperatures drop below -20°C more frequently
  - Snowfall becomes more common
  - All 4 threshold conditions are tested in training data
- Reconsider temperature threshold — -10°C may be more realistic for July-August at summit altitude
- Retrain model with larger, more diverse dataset
- Re-evaluate feature importance after retraining — expect temperature, snowfall, wind_chill, and lag features to become meaningful

---

## 11. Final Model

Trained on full 123-row dataset (not just cross-validation splits) to maximize learning before saving:

```python
final_model = XGBClassifier(n_estimators=50, max_depth=2, learning_rate=0.1, random_state=42)
final_model.fit(X, y)
joblib.dump(final_model, "elbrus_model.pkl")
```

Saved as: `E:\Portfolio_Project\elbrus_model.pkl` (44KB)

**Why train on full dataset for the saved model:**
Cross-validation was for evaluation only — those models were discarded. The final saved model uses all 123 rows so it learns from every available example before being deployed in FastAPI.

---

## 12. Scripts Created This Phase

| Script           | Purpose                                                                                                                                                                           |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `train_model.py` | Loads `features_daily`, defines X/y, runs cross-validation for both models, compares precision/recall, trains final XGBoost model, checks feature importance, saves model to disk |

## 12. There are other classification models as well. Why wouldn't consider other models?

I compared Logistic Regression and XGBoost as the two most appropriate models for this problem — one simple linear baseline and one industry-standard gradient boosting model. Given the small dataset size (123 rows), more complex models like neural networks would have been inappropriate. Random Forest was a valid alternative to XGBoost but adds limited new insight when XGBoost already outperforms on all metrics. The right next step is expanding the dataset before exploring additional models.
