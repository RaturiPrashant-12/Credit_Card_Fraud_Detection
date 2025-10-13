# fraud/utils.py
import os
import requests
import pandas as pd
from django.conf import settings
from joblib import load

# Load model once
_model = None
def get_model():
    global _model
    if _model is None:
        _model = load(settings.FRAUD_MODEL_PATH)
    return _model

def score_transaction(features: dict) -> float:
    model = get_model()
    df = pd.DataFrame([features])
    prob = float(model.predict_proba(df)[:, 1][0])
    return prob

def send_otp(phone: str) -> str:
    url = settings.FASTAPI_OTP_BASE_URL.rstrip("/") + "/send-otp"
    r = requests.post(url, json={"phone_number": phone}, timeout=10)
    r.raise_for_status()
    return r.json()["otp_id"]

def verify_otp(otp_id: str, code: str) -> bool:
    url = settings.FASTAPI_OTP_BASE_URL.rstrip("/") + "/verify-otp"
    r = requests.post(url, json={"otp_id": otp_id, "otp_code": code}, timeout=10)
    r.raise_for_status()
    return bool(r.json().get("valid"))
