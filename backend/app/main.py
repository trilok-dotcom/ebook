from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, initialize_app, firestore
import firebase_admin
from .config import ALLOWED_ORIGINS, FIREBASE_SERVICE_ACCOUNT_JSON, FIREBASE_PROJECT_ID
from .auth import verify_bearer
from .schemas import NotifyUploadBody, NotifyResult
from .notify import dispatch_notifications
import json

app = FastAPI(title="Doctor-Patient Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase Admin init
if not firebase_admin._apps:
    cred = None
    if FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            data = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(data)
        except Exception:
            # Try eval-string format if provided
            data = eval(FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(data)
    else:
        cred = credentials.ApplicationDefault()
    initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID} if FIREBASE_PROJECT_ID else None)

db = firestore.client()

@app.get("/api/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/api/notify/upload", response_model=NotifyResult)
def notify_upload(body: NotifyUploadBody, user=Depends(verify_bearer)):
    record_ref = db.collection("records").document(body.recordId)
    snap = record_ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Record not found")
    record = snap.to_dict()

    # Authorization: only the doctor who uploaded can trigger notifications
    if user.get("uid") != record.get("uploadedBy"):
        raise HTTPException(status_code=403, detail="Not allowed to notify for this record")

    # Load doctor and patient profiles
    uploaded_for = record.get("uploadedFor")
    if not uploaded_for:
        raise HTTPException(status_code=400, detail="Record missing uploadedFor")

    patient_doc = db.collection("users").document(uploaded_for).get()
    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient user not found")
    patient = patient_doc.to_dict()

    doctor_doc = db.collection("users").document(record.get("uploadedBy")).get()
    doctor = doctor_doc.to_dict() if doctor_doc.exists else {"uid": record.get("uploadedBy")}

    channels = dispatch_notifications(record, patient, doctor)
    if not channels:
        raise HTTPException(status_code=500, detail="No notification sent (config or contact missing)")

    return NotifyResult(status="sent", channels=channels)

