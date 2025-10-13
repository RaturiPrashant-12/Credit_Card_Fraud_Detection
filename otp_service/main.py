# otp_service/main.py
# FastAPI OTP microservice (Pydantic v2 • Python 3.12)

import os
import time
import uuid
import random
import traceback
from typing import Dict, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

# --- Load .env from project root, override existing envs if any ---
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

# ----- Config -----
OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "300"))       # 5 minutes
RESEND_COOLDOWN = int(os.getenv("OTP_RESEND_COOLDOWN", "60"))    # 60 seconds
MAX_ATTEMPTS     = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))

TWILIO_SID   = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# Accept either env var name and strip spaces like "+1 267 500 8164" -> "+12675008164"
TWILIO_FROM  = (os.getenv("TWILIO_FROM_NUMBER") or os.getenv("TWILIO_PHONE_NUMBER") or "").replace(" ", "")

# Optional SMS via Twilio (dev prints to console if not configured)
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
except Exception:
    TwilioClient = None  # type: ignore
    TwilioException = Exception  # type: ignore

DEV_MODE = not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and TwilioClient is not None)

# ----- App -----
app = FastAPI(title="OTP Service", version="1.2.0")

# Allow local dev from anywhere; tighten in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ----- Models (Pydantic v2) -----
class SendOtpReq(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        return v.strip()

class SendOtpResp(BaseModel):
    otp_id: str
    dev_code: Optional[str] = None  # only returned in DEV mode

class VerifyReq(BaseModel):
    otp_id: str
    otp_code: str

class VerifyResp(BaseModel):
    valid: bool

# ----- In-memory store (use Redis/db in prod) -----
STORE: Dict[str, dict] = {}               # otp_id -> {code, phone, expires_at, attempts, max_attempts}
LAST_SENT_BY_PHONE: Dict[str, float] = {} # phone -> last send ts

def _send_sms(phone: str, message: str):
    """Send SMS via Twilio if configured; otherwise print to console (dev mode)."""
    if DEV_MODE:
        print(f"[DEV SMS] to {phone}: {message}")
        return
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(body=message, from_=TWILIO_FROM, to=phone)
        print(f"[TWILIO] Sent OTP to {phone} | sid={msg.sid}")
    except TwilioException as e:
        traceback.print_exc()
        # Surface a readable error to the caller
        raise HTTPException(status_code=502, detail=f"Twilio send failed: {e.__class__.__name__}: {e}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected send error: {e.__class__.__name__}: {e}")

# ----- Convenience routes -----
@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({
        "service": "OTP Service",
        "status": "ok",
        "mode": ("dev" if DEV_MODE else "twilio"),
        "endpoints": ["/health", "/send-otp", "/verify-otp", "/docs", "/redoc"]
    })

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/health")
def health():
    # Helpful to quickly debug env loading & mode
    return {
        "status": "ok",
        "ttl": OTP_TTL_SECONDS,
        "mode": ("dev" if DEV_MODE else "twilio"),
        "sid_set": bool(TWILIO_SID),
        "token_set": bool(TWILIO_TOKEN),
        "from_set": bool(TWILIO_FROM),
    }

# ----- Core API -----
@app.post("/send-otp", response_model=SendOtpResp)
def send_otp(req: SendOtpReq):
    now = time.time()
    last = LAST_SENT_BY_PHONE.get(req.phone_number, 0.0)
    if now - last < RESEND_COOLDOWN:
        raise HTTPException(status_code=429, detail="Please wait before requesting another OTP")

    code = f"{random.randint(0, 999999):06d}"
    otp_id = uuid.uuid4().hex
    STORE[otp_id] = {
        "code": code,
        "phone": req.phone_number,
        "expires_at": now + OTP_TTL_SECONDS,
        "attempts": 0,
        "max_attempts": MAX_ATTEMPTS,
    }
    LAST_SENT_BY_PHONE[req.phone_number] = now

    _send_sms(req.phone_number, f"Your verification code is: {code}")
    return SendOtpResp(otp_id=otp_id, dev_code=(code if DEV_MODE else None))

@app.post("/verify-otp", response_model=VerifyResp)
def verify_otp(req: VerifyReq):
    item = STORE.get(req.otp_id)
    if not item:
        # Unknown otp_id
        return VerifyResp(valid=False)

    now = time.time()
    # Expired?
    if now > item.get("expires_at", 0):
        STORE.pop(req.otp_id, None)
        return VerifyResp(valid=False)

    # Attempts guard (correct key name!)
    max_attempts = int(item.get("max_attempts", MAX_ATTEMPTS))
    if int(item.get("attempts", 0)) >= max_attempts:
        STORE.pop(req.otp_id, None)
        return VerifyResp(valid=False)

    # Count this attempt
    item["attempts"] = int(item.get("attempts", 0)) + 1

    # Match?
    if req.otp_code == item.get("code"):
        STORE.pop(req.otp_id, None)  # consume on success
        return VerifyResp(valid=True)

    return VerifyResp(valid=False)