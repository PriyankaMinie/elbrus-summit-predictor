import psycopg2
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from xgboost import XGBClassifier
import joblib
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

df = pd.read_sql("SELECT * FROM features_daily ORDER BY timestamp", conn)
conn.close()

# print(df.head())
# print(df.shape)

X = df[
    [
        "temperature_c",
        "wind_speed_kmh",
        "precipitation_mm",
        "snowfall_cm",
        "wind_chill",
        "wind_lag_1",
        "temp_lag_1",
    ]
]
y = df["is_climbable"]

# Instead of one split, you do multiple splits, and average the results. - That's cross-validation

# Using Logistic Regression algorithm
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

log_reg = LogisticRegression(max_iter=1000)

metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]

print("\n===LOGISTIC REGRESSION===")
for metric in metrics:
    scores_logreg = cross_val_score(log_reg, X, y, cv=cv, scoring=metric)
    print(f"{metric}: {scores_logreg.mean():.4f}")


# Using XGBoost algorithm
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
xgb = XGBClassifier(n_estimators=50, max_depth=2, learning_rate=0.1, random_state=42)

print("\n===XGBOOST===")
for metric in metrics:
    scores_xgb = cross_val_score(xgb, X, y, cv=cv, scoring=metric)
    print(f"{metric}: {scores_xgb.mean():.4f}")


# # Train final model on full dataset
# final_model = XGBClassifier(
#     n_estimators=50, max_depth=2, learning_rate=0.1, random_state=42
# )
# final_model.fit(X, y)

# # Save model to file
# joblib.dump(final_model, "elbrus_model.pkl")
# print("Model saved to elbrus_model.pkl")


# feature_names = [
#     "temperature_c",
#     "wind_speed_kmh",
#     "precipitation_mm",
#     "snowfall_cm",
#     "wind_chill",
#     "wind_lag_1",
#     "temp_lag_1",
# ]
# importance = final_model.feature_importances_
# df_importance = pd.DataFrame({"feature": feature_names, "importance": importance})
# df_importance = df_importance.sort_values("importance", ascending=False)
# print("\nFeature Importance:")
# print(df_importance)
