import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
     "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "fraud",  
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ccfd.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "ccfd.wsgi.application"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

STATIC_URL = "static/"

# --- Custom ---
FRAUD_MODEL_PATH = os.getenv("FRAUD_MODEL_PATH", str(BASE_DIR.parent / "model" / "fraud_pipeline.joblib"))
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.5"))
FASTAPI_OTP_BASE_URL = os.getenv("FASTAPI_OTP_BASE_URL", "http://127.0.0.1:8001")


RULE_LAST_N     = int(os.getenv("RULE_LAST_N", "4"))
RULE_MIN_PREV   = int(os.getenv("RULE_MIN_PREV", "3"))
RULE_MULTIPLIER = float(os.getenv("RULE_MULTIPLIER", "3.0"))
RULE_MIN_DELTA  = float(os.getenv("RULE_MIN_DELTA", "500.0"))
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "predict"
LOGOUT_REDIRECT_URL = "login"


