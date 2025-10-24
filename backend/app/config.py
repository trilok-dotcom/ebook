import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

ALLOWED_ORIGINS: List[str] = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

BASE_APP_URL = os.getenv("BASE_APP_URL", "http://localhost:5173")

NOTIFY_CHANNELS = [c.strip().lower() for c in os.getenv("NOTIFY_CHANNELS", "email").split(",") if c.strip()]

# SendGrid
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
