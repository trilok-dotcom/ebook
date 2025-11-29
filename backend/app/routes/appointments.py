"""
Appointment routes for E-Booklet
Handles appointment booking with time slot validation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import logging
from pathlib import Path

from firebase_admin import firestore
from ..auth import verify_bearer
from ..notifications import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


class AppointmentBookRequest(BaseModel):
    """Request model for booking an appointment"""
    doctor_id: str
    doctor_name: str
    patient_name: str
    patient_email: EmailStr
    appointment_date: str  # Format: "YYYY-MM-DD"
    appointment_time: str  # Format: "HH:MM AM/PM"
    reason: Optional[str] = None
    patient_phone: Optional[str] = None


class TimeSlotCheckRequest(BaseModel):
    """Request model for checking time slot availability"""
    doctor_id: str
    appointment_date: str
    appointment_time: str


class TimeSlot(BaseModel):
    """Time slot model"""
    time: str
    available: bool
    appointment_id: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    """Request model for updating appointment status"""
    status: str  # approved, rejected, cancelled, completed
    notes: Optional[str] = None


def parse_time_slot(date_str: str, time_str: str) -> datetime:
    """
    Parse date and time strings into a datetime object
    
    Args:
        date_str: Date in format "YYYY-MM-DD" or "October 25, 2025"
        time_str: Time in format "HH:MM AM/PM" or "10:00 AM"
    
    Returns:
        datetime object
    """
    try:
        # Try parsing "YYYY-MM-DD" format first
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            # Try parsing "Month DD, YYYY" format
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
        
        # Parse time
        time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")
        
        # Combine date and time
        return datetime.combine(date_obj.date(), time_obj.time())
    except Exception as e:
        logger.error(f"Error parsing date/time: {date_str}, {time_str} - {e}")
        raise ValueError(f"Invalid date or time format: {e}")


def is_time_slot_conflict(slot1: datetime, slot2: datetime, duration_minutes: int = 30) -> bool:
    """
    Check if two time slots conflict
    
    Args:
        slot1: First appointment time
        slot2: Second appointment time
        duration_minutes: Appointment duration (default 30 minutes)
    
    Returns:
        True if slots conflict, False otherwise
    """
    # Calculate end times
    slot1_end = slot1 + timedelta(minutes=duration_minutes)
    slot2_end = slot2 + timedelta(minutes=duration_minutes)
    
    # Check for overlap
    return (slot1 < slot2_end) and (slot2 < slot1_end)


@router.post("/check-availability")
async def check_time_slot_availability(
    request: TimeSlotCheckRequest,
    user: dict = Depends(verify_bearer)
):
    """
    Check if a specific time slot is available for a doctor
    
    Args:
        request: Time slot check details
        user_id: Authenticated user ID
        
    Returns:
        dict: Availability status and conflicting appointments if any
    """
    try:
        # Parse the requested time slot
        requested_slot = parse_time_slot(request.appointment_date, request.appointment_time)
        
        # Query Firestore for existing appointments
        db = firestore.client()
        appointments_ref = db.collection('appointments')
        
        # Get all appointments for this doctor on this date
        query = appointments_ref.where('doctorId', '==', request.doctor_id).stream()
        
        conflicts = []
        for doc in query:
            appointment = doc.to_dict()
            
            # Skip cancelled or rejected appointments
            if appointment.get('status') in ['cancelled', 'rejected']:
                continue
            
            # Parse existing appointment time
            try:
                existing_slot = parse_time_slot(
                    appointment.get('date', ''),
                    appointment.get('time', '')
                )
                
                # Check for conflict (30-minute slots)
                if is_time_slot_conflict(requested_slot, existing_slot, duration_minutes=30):
                    conflicts.append({
                        "appointment_id": doc.id,
                        "patient_name": appointment.get('patientName'),
                        "time": appointment.get('time'),
                        "status": appointment.get('status')
                    })
            except ValueError:
                # Skip appointments with invalid date/time
                continue
        
        if conflicts:
            return {
                "available": False,
                "message": "This time slot is already booked",
                "conflicts": conflicts
            }
        
        return {
            "available": True,
            "message": "Time slot is available"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check availability: {str(e)}"
        )


@router.post("/book")
async def book_appointment(
    request: AppointmentBookRequest,
    user: dict = Depends(verify_bearer)
):
    """
    Book an appointment with time slot validation
    
    Args:
        request: Appointment booking details
        user_id: Authenticated user ID (patient)
        
    Returns:
        dict: Booking confirmation with appointment ID
    """
    try:
        # First, check if the time slot is available
        availability_check = TimeSlotCheckRequest(
            doctor_id=request.doctor_id,
            appointment_date=request.appointment_date,
            appointment_time=request.appointment_time
        )
        
        availability = await check_time_slot_availability(availability_check, user)
        
        if not availability["available"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Time slot not available",
                    "message": "This time slot is already booked. Please choose another time.",
                    "conflicts": availability.get("conflicts", [])
                }
            )
        
        # Create appointment in Firestore
        db = firestore.client()
        appointments_ref = db.collection('appointments')
        
        appointment_data = {
            "doctorId": request.doctor_id,
            "doctorName": request.doctor_name,
            "patientId": user['uid'],
            "patientName": request.patient_name,
            "patientEmail": request.patient_email,
            "patientPhone": request.patient_phone,
            "date": request.appointment_date,
            "time": request.appointment_time,
            "reason": request.reason,
            "status": "pending",
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Add to Firestore
        doc_ref = appointments_ref.add(appointment_data)
        appointment_id = doc_ref[1].id
        
        logger.info(f"Appointment booked: {appointment_id} for patient {user['uid']}")
        
        # Send notification to patient
        try:
            notification_service = NotificationService(db)
            
            # Prepare confirmation message
            confirmation_message = (
                f"Your appointment with {request.doctor_name} has been requested for "
                f"{request.appointment_date} at {request.appointment_time}. "
                f"You will receive a confirmation once the doctor approves it."
            )
            
            # Send SMS if phone number provided
            if request.patient_phone:
                sms_message = f"Hi {request.patient_name}, {confirmation_message} - E-Booklet"
                sms_result = await notification_service.send_sms(
                    to_phone=request.patient_phone,
                    message=sms_message,
                    patient_name=request.patient_name
                )
                logger.info(f"Appointment booking SMS sent: {sms_result}")
            
            # Send email notification
            template_path = Path(__file__).parent.parent / "notifications" / "templates" / "appointment_confirmation.html"
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_template = f.read()
                
                # Replace template variables
                html_body = html_template.replace("{{ patient_name }}", request.patient_name)
                html_body = html_body.replace("{{ patient_email }}", request.patient_email)
                html_body = html_body.replace("{{ doctor_name }}", request.doctor_name)
                html_body = html_body.replace("{{ appointment_date }}", request.appointment_date)
                html_body = html_body.replace("{{ appointment_time }}", request.appointment_time)
                html_body = html_body.replace("{{ appointment_reason }}", request.reason or "General consultation")
                html_body = html_body.replace("{{ dashboard_url }}", "http://localhost:5173/patient")
                
                email_result = await notification_service.send_email(
                    to_email=request.patient_email,
                    subject="Appointment Request Received - E-Booklet",
                    html_body=html_body,
                    patient_name=request.patient_name
                )
                logger.info(f"Appointment booking email sent: {email_result}")
                
        except Exception as e:
            logger.error(f"Failed to send appointment notification: {str(e)}")
            # Don't fail the booking if notification fails
        
        return {
            "success": True,
            "message": "Appointment booked successfully",
            "appointment_id": appointment_id,
            "appointment": {
                **appointment_data,
                "id": appointment_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to book appointment: {str(e)}"
        )


@router.get("/available-slots/{doctor_id}")
async def get_available_slots(
    doctor_id: str,
    date: str,  # Format: YYYY-MM-DD
    user: dict = Depends(verify_bearer)
):
    """
    Get all available time slots for a doctor on a specific date
    
    Args:
        doctor_id: Doctor's user ID
        date: Date in YYYY-MM-DD format
        user_id: Authenticated user ID
        
    Returns:
        List of available time slots
    """
    try:
        # Define working hours (9 AM to 5 PM, 30-minute slots)
        working_hours_start = 9  # 9 AM
        working_hours_end = 17   # 5 PM
        slot_duration = 30  # minutes
        
        # Generate all possible time slots
        all_slots = []
        current_time = datetime.strptime(f"{date} {working_hours_start:02d}:00", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{date} {working_hours_end:02d}:00", "%Y-%m-%d %H:%M")
        
        while current_time < end_time:
            time_str = current_time.strftime("%I:%M %p")
            all_slots.append({
                "time": time_str,
                "datetime": current_time,
                "available": True
            })
            current_time += timedelta(minutes=slot_duration)
        
        # Get existing appointments for this doctor on this date
        db = firestore.client()
        appointments_ref = db.collection('appointments')
        query = appointments_ref.where('doctorId', '==', doctor_id).stream()
        
        # Mark booked slots as unavailable
        for doc in query:
            appointment = doc.to_dict()
            
            # Skip cancelled or rejected appointments
            if appointment.get('status') in ['cancelled', 'rejected']:
                continue
            
            try:
                appointment_date = appointment.get('date', '')
                appointment_time = appointment.get('time', '')
                
                # Only process appointments for the requested date
                if date in appointment_date or appointment_date in date:
                    appointment_dt = parse_time_slot(appointment_date, appointment_time)
                    
                    # Mark conflicting slots as unavailable
                    for slot in all_slots:
                        if is_time_slot_conflict(slot["datetime"], appointment_dt, slot_duration):
                            slot["available"] = False
                            slot["appointment_id"] = doc.id
                            slot["status"] = appointment.get('status')
            except ValueError:
                continue
        
        # Remove datetime objects before returning (not JSON serializable)
        result_slots = [
            {
                "time": slot["time"],
                "available": slot["available"],
                "appointment_id": slot.get("appointment_id"),
                "status": slot.get("status")
            }
            for slot in all_slots
        ]
        
        return {
            "date": date,
            "doctor_id": doctor_id,
            "slots": result_slots,
            "total_slots": len(result_slots),
            "available_slots": sum(1 for s in result_slots if s["available"])
        }
        
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available slots: {str(e)}"
        )


@router.get("/my-appointments")
async def get_my_appointments(
    user: dict = Depends(verify_bearer)
):
    """
    Get all appointments for the current user (patient or doctor)
    
    Args:
        user_id: Authenticated user ID
        
    Returns:
        List of appointments
    """
    try:
        db = firestore.client()
        appointments_ref = db.collection('appointments')
        
        # Get user profile to determine role
        user_ref = db.collection('users').document(user['uid'])
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        user_role = user_data.get('role')
        
        # Query based on role
        if user_role == 'doctor':
            query = appointments_ref.where('doctorId', '==', user['uid']).stream()
        else:  # patient
            query = appointments_ref.where('patientId', '==', user['uid']).stream()
        
        appointments = []
        for doc in query:
            appointment = doc.to_dict()
            appointment['id'] = doc.id
            appointments.append(appointment)
        
        # Sort by date and time (most recent first)
        appointments.sort(
            key=lambda x: (x.get('date', ''), x.get('time', '')),
            reverse=True
        )
        
        return {
            "appointments": appointments,
            "total": len(appointments)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get appointments: {str(e)}"
        )


@router.put("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    request: AppointmentStatusUpdate,
    user: dict = Depends(verify_bearer)
):
    """
    Update appointment status (approve, reject, cancel, complete)
    Sends SMS and email notifications to the patient
    
    Args:
        appointment_id: Appointment ID
        request: Status update details
        user: Authenticated user (doctor or patient)
        
    Returns:
        dict: Updated appointment details
    """
    try:
        db = firestore.client()
        
        # Get appointment
        appointment_ref = db.collection('appointments').document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment = appointment_doc.to_dict()
        
        # Verify user has permission to update
        user_ref = db.collection('users').document(user['uid'])
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        user_role = user_data.get('role')
        
        # Only doctor can approve/reject, patient can cancel
        if request.status in ['approved', 'rejected'] and user_role != 'doctor':
            raise HTTPException(status_code=403, detail="Only doctors can approve or reject appointments")
        
        if request.status == 'cancelled' and appointment.get('patientId') != user['uid'] and user_role != 'doctor':
            raise HTTPException(status_code=403, detail="You can only cancel your own appointments")
        
        # Update appointment status
        update_data = {
            "status": request.status,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        if request.notes:
            update_data["statusNotes"] = request.notes
        
        appointment_ref.update(update_data)
        
        logger.info(f"Appointment {appointment_id} status updated to {request.status}")
        
        # Send notification to patient
        try:
            notification_service = NotificationService(db)
            
            # Get patient details
            patient_ref = db.collection('users').document(appointment.get('patientId'))
            patient_doc = patient_ref.get()
            
            if patient_doc.exists:
                patient_data = patient_doc.to_dict()
                patient_email = patient_data.get('email') or appointment.get('patientEmail')
                patient_phone = patient_data.get('phone') or appointment.get('patientPhone')
                patient_name = appointment.get('patientName', 'Patient')
                doctor_name = appointment.get('doctorName', 'Doctor')
                
                # Prepare notification message based on status
                status_messages = {
                    'approved': f"Your appointment with {doctor_name} on {appointment.get('date')} at {appointment.get('time')} has been approved! ✅",
                    'rejected': f"Your appointment request with {doctor_name} on {appointment.get('date')} at {appointment.get('time')} has been declined. Please contact the clinic for more information.",
                    'cancelled': f"Your appointment with {doctor_name} on {appointment.get('date')} at {appointment.get('time')} has been cancelled.",
                    'completed': f"Your appointment with {doctor_name} has been marked as completed. Thank you for visiting!"
                }
                
                message = status_messages.get(request.status, f"Your appointment status has been updated to {request.status}")
                
                if request.notes:
                    message += f"\n\nNote: {request.notes}"
                
                # Send SMS if phone number available
                if patient_phone:
                    sms_message = f"Hi {patient_name}, {message} - E-Booklet"
                    sms_result = await notification_service.send_sms(
                        to_phone=patient_phone,
                        message=sms_message,
                        patient_name=patient_name
                    )
                    logger.info(f"SMS notification sent: {sms_result}")
                
                # Send email notification
                if patient_email:
                    # Load email template
                    template_path = Path(__file__).parent.parent / "notifications" / "templates" / "general_notification.html"
                    
                    if template_path.exists():
                        with open(template_path, 'r', encoding='utf-8') as f:
                            html_template = f.read()
                        
                        html_body = html_template.replace("{{ patient_name }}", patient_name)
                        html_body = html_body.replace("{{ patient_email }}", patient_email)
                        html_body = html_body.replace("{{ message_body }}", message)
                        html_body = html_body.replace("{% if cta_url %}", "")
                        html_body = html_body.replace("{% endif %}", "")
                        
                        email_subject = f"Appointment {request.status.title()} - E-Booklet"
                        
                        email_result = await notification_service.send_email(
                            to_email=patient_email,
                            subject=email_subject,
                            html_body=html_body,
                            patient_name=patient_name
                        )
                        logger.info(f"Email notification sent: {email_result}")
                
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            # Don't fail the status update if notification fails
        
        # Get updated appointment
        updated_appointment = appointment_ref.get().to_dict()
        updated_appointment['id'] = appointment_id
        
        return {
            "success": True,
            "message": f"Appointment {request.status} successfully",
            "appointment": updated_appointment
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update appointment status: {str(e)}"
        )
