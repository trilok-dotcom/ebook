# FastAPI Backend for Notifications

## Features
- Firebase Admin verification of Firebase ID tokens
- CORS for frontend origins
- POST /api/notify/upload: sends notification (email/SMS) to patient for a record
- GET /api/healthz

## Setup
1. Create a Firebase service account (Editor) and download JSON.
2. Copy `.env.example` to `.env` and fill values.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run locally:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Environment
- `ALLOWED_ORIGINS`: comma-separated list of frontend URLs.
- `FIREBASE_SERVICE_ACCOUNT_JSON`: embed JSON string of service account.
- `FIREBASE_PROJECT_ID`: your Firebase project id.
- `BASE_APP_URL`: frontend base for links in notifications.
- `NOTIFY_CHANNELS`: comma list, e.g., `email`, `sms`, or `email,sms`.
- `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`: for email
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`: for SMS

## Request Auth
Send `Authorization: Bearer <firebase_id_token>` header from the frontend after the user signs in.

## Notify Upload
- Body: `{ "recordId": "<firestore id>" }`
- Only the record's `uploadedBy` user can trigger notifications.

## Deploy
- Recommended: Render or Railway.
- Set env vars from `.env` into the platform.
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
