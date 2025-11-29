"""
Notification routes for E-Booklet
Handles appointment and record upload notifications
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging
from pathlib import Path

from ..notifications import NotificationService
from ..auth import verify_bearer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notify", tags=["notifications"])


class AppointmentNotificationRequest(BaseModel):
    """Request model for appointment notifications"""
    patient_name: str
    patient_email: EmailStr
    patient_phone: Optional[str] = None
    doctor_name: str
    appointment_date: str
    appointment_time: str
    appointment_reason: Optional[str] = None


class RecordNotificationRequest(BaseModel):
    """Request model for record upload notifications"""
    patient_name: str
    patient_email: EmailStr
    patient_phone: Optional[str] = None
    doctor_name: str
    record_name: str
    record_type: str = "Medical Record"
    notes: Optional[str] = None


class TestNotificationRequest(BaseModel):
    """Request model for test notifications"""
    email: EmailStr
    phone: Optional[str] = None


@router.post("/appointment")
async def send_appointment_notification(
    request: AppointmentNotificationRequest,
    user: dict = Depends(verify_bearer)
):
    """
    Send appointment confirmation via email and SMS
    
    Args:
        request: Appointment notification details
        user_id: Authenticated user ID from Firebase token
        
    Returns:
        dict: Status of email and SMS delivery
    """
    try:
        logger.info(f"Sending appointment notification to {request.patient_email}")
        
        # Initialize notification service
        from firebase_admin import firestore
        db = firestore.client()
        notification_service = NotificationService(db)
        
        # Prepare email template data
        template_data = {
            "patient_name": request.patient_name,
            "patient_email": request.patient_email,
            "doctor_name": request.doctor_name,
            "appointment_date": request.appointment_date,
            "appointment_time": request.appointment_time,
            "appointment_reason": request.appointment_reason,
            "dashboard_url": "http://localhost:5173/patient"  # Update with your actual URL
        }
        
        # Load HTML template
        template_path = Path(__file__).parent.parent / "notifications" / "templates" / "appointment_confirmation.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        # Replace template variables
        html_body = html_template
        for key, value in template_data.items():
            if value:
                html_body = html_body.replace(f"{{{{ {key} }}}}", str(value))
            else:
                # Remove optional sections if value is None
                html_body = html_body.replace(f"{{% if {key} %}}", "")
                html_body = html_body.replace(f"{{% endif %}}", "")
        
        # Send email notification
        email_result = await notification_service.send_email(
            to_email=request.patient_email,
            subject=f"Your Appointment is Confirmed 🩺",
            html_body=html_body,
            patient_name=request.patient_name
        )
        
        # Send SMS notification if phone number provided
        sms_result = {"success": False, "message": "Phone number not provided"}
        if request.patient_phone:
            sms_message = (
                f"Hi {request.patient_name}, your appointment with {request.doctor_name} "
                f"on {request.appointment_date} at {request.appointment_time} is confirmed. - E-Booklet"
            )
            sms_result = await notification_service.send_sms(
                to_phone=request.patient_phone,
                message=sms_message,
                patient_name=request.patient_name
            )
        
        return {
            "success": True,
            "message": "Appointment notification sent successfully",
            "email": email_result,
            "sms": sms_result
        }
        
    except Exception as e:
        logger.error(f"Error sending appointment notification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send appointment notification: {str(e)}"
        )


@router.post("/record")
async def send_record_notification(
    request: RecordNotificationRequest,
    user: dict = Depends(verify_bearer)
):
    """
    Send record upload notification via email and SMS
    
    Args:
        request: Record notification details
        user_id: Authenticated user ID from Firebase token
        
    Returns:
        dict: Status of email and SMS delivery
    """
    try:
        logger.info(f"Sending record notification to {request.patient_email}")
        
        # Initialize notification service
        from firebase_admin import firestore
        db = firestore.client()
        notification_service = NotificationService(db)
        
        # Prepare email template data
        template_data = {
            "patient_name": request.patient_name,
            "patient_email": request.patient_email,
            "doctor_name": request.doctor_name,
            "record_name": request.record_name,
            "record_type": request.record_type,
            "upload_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "notes": request.notes,
            "dashboard_url": "http://localhost:5173/patient"  # Update with your actual URL
        }
        
        # Load HTML template
        template_path = Path(__file__).parent.parent / "notifications" / "templates" / "record_uploaded.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        # Replace template variables
        html_body = html_template
        for key, value in template_data.items():
            if value:
                html_body = html_body.replace(f"{{{{ {key} }}}}", str(value))
            else:
                # Remove optional sections if value is None
                html_body = html_body.replace(f"{{% if {key} %}}", "")
                html_body = html_body.replace(f"{{% endif %}}", "")
        
        # Send email notification
        email_result = await notification_service.send_email(
            to_email=request.patient_email,
            subject=f"New Health Record Uploaded 📄",
            html_body=html_body,
            patient_name=request.patient_name
        )
        
        # Send SMS notification if phone number provided
        sms_result = {"success": False, "message": "Phone number not provided"}
        if request.patient_phone:
            sms_message = (
                f"Hi {request.patient_name}, a new health record \"{request.record_name}\" "
                f"has been added to your profile. Check your app. - E-Booklet"
            )
            sms_result = await notification_service.send_sms(
                to_phone=request.patient_phone,
                message=sms_message,
                patient_name=request.patient_name
            )
        
        return {
            "success": True,
            "message": "Record notification sent successfully",
            "email": email_result,
            "sms": sms_result
        }
        
    except Exception as e:
        logger.error(f"Error sending record notification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send record notification: {str(e)}"
        )


@router.post("/test")
async def test_notification(
    request: TestNotificationRequest
):
    """
    Test endpoint to verify notification service is working
    Does not require authentication
    """
    try:
        # Initialize notification service
        from firebase_admin import firestore
        db = firestore.client()
        notification_service = NotificationService(db)
        
        # Send test email
        template_path = Path(__file__).parent.parent / "notifications" / "templates" / "general_notification.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        html_body = html_template.replace("{{ patient_name }}", "Test User")
        html_body = html_body.replace("{{ patient_email }}", request.email)
        html_body = html_body.replace("{{ message_body }}", 
            "This is a test notification from E-Booklet. If you received this, your notification system is working correctly!")
        html_body = html_body.replace("{% if cta_url %}", "")
        html_body = html_body.replace("{% endif %}", "")
        
        email_result = await notification_service.send_email(
            to_email=request.email,
            subject="Test Notification from E-Booklet ✨",
            html_body=html_body,
            patient_name="Test User"
        )
        
        sms_result = {"success": False, "message": "Phone number not provided"}
        if request.phone:
            sms_result = await notification_service.send_sms(
                to_phone=request.phone,
                message="Appointment is booked successfully. - E-Booklet",
                patient_name="Test User"
            )
        
        return {
            "success": True,
            "message": "Test notification sent",
            "email": email_result,
            "sms": sms_result
        }
        
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test notification: {str(e)}"
        )
