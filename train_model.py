# train_model.py — minimal features to match the new form
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
    "/Users/prashantraturi/Desktop/Projects_Placements/Credit_Card_Django/datalab_export_2024-09-30 13_43_39.csv",
)
TARGET = "is_fraud"

MODEL_OUT = Path("model/fraud_pipeline.joblib")
MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)

# ---- Feature engineering to align with the new form ----
# We only keep: category, amt, city, state, job, hour, dow, age
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Parse timestamps and DOB if present so we can compute hour/dow/age from data
    if "trans_date_trans_time" in df.columns:
        dt = pd.to_datetime(df["trans_date_trans_time"], errors="coerce")
        df["hour"] = dt.dt.hour
        df["dow"] = dt.dt.dayofweek
    else:
        # if not present, default safely
        df["hour"] = 0
        df["dow"] = 0

    if "dob" in df.columns and "trans_date_trans_time" in df.columns:
        dob = pd.to_datetime(df["dob"], errors="coerce")
        dt  = pd.to_datetime(df["trans_date_trans_time"], errors="coerce")
        df["age"] = ((dt - dob).dt.days / 365.25).clip(lower=0)
    elif "age" not in df.columns:
        df["age"] = np.nan  # will be imputed by model if you add imputer; here we expect 'age' exists in CSV

    # Keep only the fields we actually collect now
    keep = ["category", "amt", "city", "state", "job", "hour", "dow", "age", TARGET]
    missing = [c for c in keep if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    return df[keep]

def main():
    df = pd.read_csv(CSV_PATH)
    assert TARGET in df.columns, f"Target '{TARGET}' not in dataset"

    df = build_features(df).dropna(subset=[TARGET])

    y = df[TARGET].astype(int)
    X = df.drop(columns=[TARGET])

    # Explicit feature lists to lock schema
    numeric_features = ["amt", "hour", "dow", "age"]
    categorical_features = ["category", "city", "state", "job"]

    preproc = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(with_mean=False), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
        ],
        remainder="drop",
    )

    clf = LogisticRegression(max_iter=300, class_weight="balanced")

    pipe = Pipeline(steps=[("preproc", preproc), ("clf", clf)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipe.fit(X_train, y_train)
    y_prob = pipe.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    print("ROC AUC:", round(roc_auc_score(y_test, y_prob), 4))
    print(classification_report(y_test, y_pred, digits=4))

    dump(pipe, MODEL_OUT)
    print(f"Saved pipeline -> {MODEL_OUT.resolve()}")

if __name__ == "__main__":
    main()
