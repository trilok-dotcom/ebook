from typing import Dict, List
from .config import (
    NOTIFY_CHANNELS,
    SENDGRID_API_KEY,
    SENDGRID_FROM_EMAIL,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    BASE_APP_URL,
)

# Lazy imports to avoid mandatory deps when not used
_sendgrid = None
_twilio_client = None

def _ensure_sendgrid():
    global _sendgrid
    if _sendgrid is None:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        _sendgrid = (SendGridAPIClient(SENDGRID_API_KEY), Mail)
    return _sendgrid


def _ensure_twilio():
    global _twilio_client
    if _twilio_client is None:
        from twilio.rest import Client
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


def build_message(record: Dict, patient: Dict, doctor: Dict) -> Dict:
    doctor_name = doctor.get("displayName") or doctor.get("email") or "Your doctor"
    file_type = record.get("fileType", "record")
    title = f"New {file_type} uploaded by {doctor_name}"
    body = (
        f"Hello {patient.get('displayName') or patient.get('email')},\n\n"
        f"A new {file_type} has been uploaded for you by {doctor_name}.\n"
        f"Notes: {record.get('notes') or '—'}\n\n"
        f"View it here: {BASE_APP_URL}/patient/records\n\n"
        f"If you did not expect this, please contact your provider."
    )
    return {"title": title, "body": body}


def send_email(to_email: str, subject: str, body: str) -> str:
    if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
        raise RuntimeError("SendGrid not configured")
    client, Mail = _ensure_sendgrid()
    message = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )
    resp = client.send(message)
    return str(resp.headers.get("X-Message-Id") or resp.status_code)


def send_sms(to_number: str, body: str) -> str:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_FROM_NUMBER:
        raise RuntimeError("Twilio not configured")
    client = _ensure_twilio()
    msg = client.messages.create(
        from_=TWILIO_FROM_NUMBER,
        to=to_number,
        body=body,
    )
    return msg.sid


def dispatch_notifications(record: Dict, patient: Dict, doctor: Dict) -> List[str]:
    sent_channels: List[str] = []
    msg = build_message(record, patient, doctor)
    # Try Email
    if "email" in NOTIFY_CHANNELS and patient.get("email"):
        try:
            send_email(patient["email"], msg["title"], msg["body"])
            sent_channels.append("email")
        except Exception:
            pass
    # Try SMS if phone exists
    patient_phone = patient.get("phone") or patient.get("phoneNumber")
    if "sms" in NOTIFY_CHANNELS and patient_phone:
        try:
            send_sms(patient_phone, msg["body"])
            sent_channels.append("sms")
        except Exception:
            pass
    return sent_channels
