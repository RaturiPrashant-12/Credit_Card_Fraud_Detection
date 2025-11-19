# train_model.py — updated version without state, job, or age
import os
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from joblib import dump

# ---- Config ----
CSV_PATH = os.getenv(
    "DATA_CSV_PATH",
    "/Users/prashantraturi/Desktop/Projects_Placements/Credit_Card_Django /datalab_export_2024-09-30 13_43_39.csv",)
TARGET = "is_fraud"

MODEL_OUT = Path("model/fraud_pipeline.joblib")
MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)


# ---- Feature Engineering (matching new form) ----
# We now only use: category, amt, city, hour, dow
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Extract hour and day of week if timestamp exists
    if "trans_date_trans_time" in df.columns:
        dt = pd.to_datetime(df["trans_date_trans_time"], errors="coerce")
        df["hour"] = dt.dt.hour.fillna(0).astype(int)
        df["dow"] = dt.dt.dayofweek.fillna(0).astype(int)
    else:
        # fallback defaults
        df["hour"] = 0
        df["dow"] = 0

    # Keep only required columns (ignore card info and removed features)
    keep = ["category", "amt", "city", "hour", "dow", TARGET]
    missing = [c for c in keep if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    return df[keep]


def main():
    # Load dataset
    df = pd.read_csv(CSV_PATH)
    assert TARGET in df.columns, f"Target '{TARGET}' not in dataset"

    df = build_features(df).dropna(subset=[TARGET])

    y = df[TARGET].astype(int)
    X = df.drop(columns=[TARGET])

    # Define preprocessing
    numeric_features = ["amt", "hour", "dow"]
    categorical_features = ["category", "city"]

    preproc = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(with_mean=False), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ],
        remainder="drop",
    )

    # Logistic Regression (balanced for fraud detection)
    clf = LogisticRegression(max_iter=300, class_weight="balanced")

    pipe = Pipeline(steps=[("preproc", preproc), ("clf", clf)])

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Train model
    pipe.fit(X_train, y_train)

    # Evaluate
    y_prob = pipe.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    print("✅ Model trained successfully!")
    print("ROC AUC:", round(roc_auc_score(y_test, y_prob), 4))
    print(classification_report(y_test, y_pred, digits=4))

    # Save model
    dump(pipe, MODEL_OUT)
    print(f"💾 Saved model pipeline → {MODEL_OUT.resolve()}")


if __name__ == "__main__":
    main()
