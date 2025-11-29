import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import firebase_admin
from firebase_admin import credentials, firestore

from .config import settings
from .auth import verify_bearer
from .models import (
    NotifyUploadRequest,
    NotifyResult,
    HealthCheckResponse,
    CreateRecordRequest,
    RecordResponse
)
from .notifications import NotificationService
from .database import DatabaseService
from .routes import notifications, appointments

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global services
db_service: DatabaseService = None
notification_service: NotificationService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_service, notification_service
    
    # Startup
    logger.info("Starting application...")
    
    # Validate configuration
    try:
        validate_config()
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise
    
    # Initialize Firebase
    try:
        initialize_firebase()
        db = firestore.client()
        db_service = DatabaseService(db)
        notification_service = NotificationService(db)
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")
        raise
    
    logger.info(f"Application started in {settings.ENVIRONMENT} mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    firebase_admin.delete_app(firebase_admin.get_app())


app = FastAPI(
    title="Healthcare Records API",
    description="API for managing doctor-patient medical records",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Include routers
app.include_router(notifications.router)
app.include_router(appointments.router)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req-{datetime.utcnow().timestamp()}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


def validate_config():
    """Validate application configuration"""
    errors = []
    
    if not settings.FIREBASE_PROJECT_ID:
        errors.append("FIREBASE_PROJECT_ID is required")
    
    if not settings.FIREBASE_SERVICE_ACCOUNT_JSON and not settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        errors.append("Either FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_PATH is required")
    
    # Validate notification configuration
    notification_errors = settings.validate_notification_config()
    errors.extend(notification_errors)
    
    if errors:
        raise RuntimeError(
            "Configuration validation failed:\n" +
            "\n".join(f"  - {error}" for error in errors)
        )


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if firebase_admin._apps:
        logger.info("Firebase already initialized")
        return
    
    cred = None
    
    # Try JSON string first
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            data = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(data)
            logger.info("Using Firebase credentials from JSON string")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT_JSON format: {str(e)}")
    
    # Try file path
    elif settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        try:
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            logger.info(f"Using Firebase credentials from file: {settings.FIREBASE_SERVICE_ACCOUNT_PATH}")
        except Exception as e:
            raise ValueError(f"Failed to load Firebase credentials from file: {str(e)}")
    
    # Use application default credentials
    else:
        cred = credentials.ApplicationDefault()
        logger.info("Using Firebase Application Default Credentials")
    
    firebase_admin.initialize_app(
        cred,
        {"projectId": settings.FIREBASE_PROJECT_ID}
    )


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/api/healthz", response_model=HealthCheckResponse)
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return HealthCheckResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        environment=settings.ENVIRONMENT
    )


@app.get("/api/me")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_current_user(request: Request, user=Depends(verify_bearer)):
    """Get current user profile"""
    try:
        user_profile = await db_service.get_user(user["uid"])
        
        if not user_profile:
            # Create user if doesn't exist
            user_profile = await db_service.create_user(
                uid=user["uid"],
                user_data={
                    "email": user.get("email"),
                    "displayName": user.get("name"),
                    "photoURL": user.get("picture"),
                    "role": "patient",  # Default role
                    "preferences": {
                        "emailNotifications": True,
                        "smsNotifications": True,
                        "pushNotifications": True
                    }
                }
            )
        
        return user_profile
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")


@app.post("/api/notify/upload", response_model=NotifyResult)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def notify_upload(
    request: Request,
    body: NotifyUploadRequest,
    user=Depends(verify_bearer)
):
    """Send notification for uploaded record"""
    try:
        # Get record
        record = await db_service.get_record(body.recordId)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Authorization: only the doctor who uploaded can trigger notifications
        if user.get("uid") != record.get("uploadedBy"):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to send notifications for this record"
            )
        
        # Get patient and doctor profiles
        patient = await db_service.get_user(record["uploadedFor"])
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        doctor = await db_service.get_user(record["uploadedBy"])
        if not doctor:
            doctor = {"uid": record["uploadedBy"], "email": user.get("email")}
        
        # Send notifications
        result = await notification_service.send_notification(record, patient, doctor)
        
        # Create audit log
        await db_service.create_audit_log({
            "action": "notification_sent",
            "userId": doctor["uid"],
            "targetUserId": patient["uid"],
            "resourceType": "record",
            "resourceId": body.recordId,
            "details": result,
            "ipAddress": request.client.host,
            "userAgent": request.headers.get("user-agent", "")
        })
        
        return NotifyResult(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send notification")


@app.get("/api/records/patient/{patient_uid}")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_patient_records(
    request: Request,
    patient_uid: str,
    limit: int = 50,
    offset: int = 0,
    user=Depends(verify_bearer)
):
    """Get records for a patient"""
    try:
        # Authorization: user must be the patient or their doctor
        if user["uid"] != patient_uid:
            # TODO: Check if user is patient's doctor
            raise HTTPException(status_code=403, detail="Not authorized")
        
        records = await db_service.get_patient_records(patient_uid, limit, offset)
        return {"records": records, "count": len(records)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient records: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch records")


@app.get("/api/records/doctor/{doctor_uid}")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_doctor_records(
    request: Request,
    doctor_uid: str,
    limit: int = 50,
    offset: int = 0,
    user=Depends(verify_bearer)
):
    """Get records uploaded by a doctor"""
    try:
        # Authorization: user must be the doctor
        if user["uid"] != doctor_uid:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        records = await db_service.get_doctor_records(doctor_uid, limit, offset)
        return {"records": records, "count": len(records)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching doctor records: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch records")


@app.get("/api/notifications")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_notifications(
    request: Request,
    unread_only: bool = False,
    limit: int = 50,
    user=Depends(verify_bearer)
):
    """Get notifications for current user"""
    try:
        notifications = await db_service.get_user_notifications(
            user["uid"],
            unread_only=unread_only,
            limit=limit
        )
        return {"notifications": notifications, "count": len(notifications)}
    
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


@app.patch("/api/notifications/{notification_id}/read")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def mark_notification_read(
    request: Request,
    notification_id: str,
    user=Depends(verify_bearer)
):
    """Mark notification as read"""
    try:
        await db_service.mark_notification_read(notification_id)
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )