import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .providers import EmailProvider, SMSProvider
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to patients"""
    
    def __init__(self, db):
        self.db = db
        self.email_provider = EmailProvider()
        self.sms_provider = SMSProvider() if self._is_sms_configured() else None
    
    def _is_sms_configured(self) -> bool:
        """Check if SMS is configured"""
        return all([
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_FROM_NUMBER
        ])
    
    async def send_notification(
        self,
        record: Dict[str, Any],
        patient: Dict[str, Any],
        doctor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notification to patient about new medical record
        
        Args:
            record: Medical record document
            patient: Patient user document
            doctor: Doctor user document
        
        Returns:
            Dict with notification status
        """
        results = {
            "email": None,
            "sms": None,
            "sent_at": datetime.utcnow().isoformat()
        }
        
        # Get patient preferences
        preferences = patient.get("preferences", {})
        email_enabled = preferences.get("emailNotifications", True)
        sms_enabled = preferences.get("smsNotifications", False)
        
        # Send Email Notification
        if email_enabled and patient.get("email"):
            try:
                email_result = await self._send_email_notification(record, patient, doctor)
                results["email"] = email_result
                logger.info(f"✅ Email notification sent to {patient['email']}")
            except Exception as e:
                logger.error(f"❌ Failed to send email to {patient['email']}: {str(e)}")
                results["email"] = {"success": False, "error": str(e)}
        else:
            logger.info(f"ℹ️  Email notification skipped for {patient.get('email', 'unknown')}")
        
        # Send SMS Notification
        if sms_enabled and patient.get("phone") and self.sms_provider:
            try:
                sms_result = await self._send_sms_notification(record, patient, doctor)
                results["sms"] = sms_result
                logger.info(f"✅ SMS notification sent to {patient['phone']}")
            except Exception as e:
                logger.error(f"❌ Failed to send SMS to {patient['phone']}: {str(e)}")
                results["sms"] = {"success": False, "error": str(e)}
        else:
            logger.info(f"ℹ️  SMS notification skipped for {patient.get('phone', 'unknown')}")
        
        # Store notification in Firestore
        await self._create_notification_record(record, patient, doctor, results)
        
        return results
    
    async def _send_email_notification(
        self,
        record: Dict[str, Any],
        patient: Dict[str, Any],
        doctor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email notification with beautiful template"""
        
        # Prepare email data
        patient_name = patient.get("displayName", patient.get("email", "Patient"))
        doctor_name = doctor.get("displayName", doctor.get("email", "Your Doctor"))
        record_type = record.get("fileType", "medical record").title()
        file_name = record.get("fileName", "document")
        upload_date = self._format_date(record.get("uploadedAt"))
        notes = record.get("notes", "")
        
        # Generate view link
        view_link = f"{settings.BASE_APP_URL}/patient"
        
        # Email subject
        subject = f"📋 New {record_type} from {doctor_name}"
        
        # Plain text body
        plain_body = self._generate_plain_text_email(
            patient_name, doctor_name, record_type, file_name, upload_date, notes, view_link
        )
        
        # HTML body (beautiful template)
        html_body = self._generate_html_email(
            patient_name, doctor_name, record_type, file_name, upload_date, notes, view_link
        )
        
        # Send email
        return await self.email_provider.send(
            to=patient["email"],
            subject=subject,
            body=html_body
        )
    
    def _generate_plain_text_email(
        self, patient_name: str, doctor_name: str, record_type: str,
        file_name: str, upload_date: str, notes: str, view_link: str
    ) -> str:
        """Generate plain text email"""
        text = f"""
Hello {patient_name},

You have received a new medical record from {doctor_name}.

📋 Record Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Type: {record_type}
• File: {file_name}
• Uploaded: {upload_date}
• From: {doctor_name}
"""
        
        if notes:
            text += f"\n💬 Doctor's Notes:\n{notes}\n"
        
        text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 View Your Record:
{view_link}

Please log in to your account to view and download the complete record.

---
This is an automated notification from Healthcare Records System.
If you have any questions, please contact {doctor_name} directly.

Best regards,
Healthcare Records Team
"""
        return text.strip()
    
    def _generate_html_email(
        self, patient_name: str, doctor_name: str, record_type: str,
        file_name: str, upload_date: str, notes: str, view_link: str
    ) -> str:
        """Generate beautiful HTML email template"""
        
        notes_html = ""
        if notes:
            notes_html = f"""
            <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 16px; margin: 20px 0; border-radius: 8px;">
                <h3 style="margin: 0 0 8px 0; color: #92400E; font-size: 14px; font-weight: 600;">
                    💬 Doctor's Notes
                </h3>
                <p style="margin: 0; color: #78350F; font-size: 14px; line-height: 1.6;">
                    {notes}
                </p>
            </div>
            """
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Medical Record</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #F3F4F6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F3F4F6; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFFFF; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #FFFFFF; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                🏥 Healthcare Records
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #E0E7FF; font-size: 16px;">
                                New Medical Record Available
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            
                            <!-- Greeting -->
                            <p style="margin: 0 0 24px 0; color: #111827; font-size: 16px; line-height: 1.6;">
                                Hello <strong>{patient_name}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 30px 0; color: #4B5563; font-size: 16px; line-height: 1.6;">
                                You have received a new medical record from <strong style="color: #667eea;">{doctor_name}</strong>.
                            </p>
                            
                            <!-- Record Details Card -->
                            <div style="background-color: #F9FAFB; border: 2px solid #E5E7EB; border-radius: 10px; padding: 24px; margin: 24px 0;">
                                <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 18px; font-weight: 600;">
                                    📋 Record Details
                                </h2>
                                
                                <table width="100%" cellpadding="8" cellspacing="0">
                                    <tr>
                                        <td style="color: #6B7280; font-size: 14px; width: 120px;">
                                            <strong>Type:</strong>
                                        </td>
                                        <td style="color: #111827; font-size: 14px;">
                                            <span style="background-color: #DBEAFE; color: #1E40AF; padding: 4px 12px; border-radius: 20px; font-weight: 600;">
                                                {record_type}
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="color: #6B7280; font-size: 14px; padding-top: 8px;">
                                            <strong>File Name:</strong>
                                        </td>
                                        <td style="color: #111827; font-size: 14px; padding-top: 8px;">
                                            {file_name}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="color: #6B7280; font-size: 14px; padding-top: 8px;">
                                            <strong>Uploaded:</strong>
                                        </td>
                                        <td style="color: #111827; font-size: 14px; padding-top: 8px;">
                                            {upload_date}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="color: #6B7280; font-size: 14px; padding-top: 8px;">
                                            <strong>From:</strong>
                                        </td>
                                        <td style="color: #111827; font-size: 14px; padding-top: 8px;">
                                            {doctor_name}
                                        </td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- Doctor's Notes (if any) -->
                            {notes_html}
                            
                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{view_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #FFFFFF; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                            🔍 View Your Record
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 24px 0 0 0; color: #6B7280; font-size: 14px; line-height: 1.6; text-align: center;">
                                Please log in to your account to view and download the complete record.
                            </p>
                            
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F9FAFB; padding: 30px; text-align: center; border-top: 1px solid #E5E7EB;">
                            <p style="margin: 0 0 8px 0; color: #6B7280; font-size: 13px;">
                                This is an automated notification from Healthcare Records System.
                            </p>
                            <p style="margin: 0; color: #6B7280; font-size: 13px;">
                                If you have any questions, please contact {doctor_name} directly.
                            </p>
                            <p style="margin: 16px 0 0 0; color: #9CA3AF; font-size: 12px;">
                                © 2025 Healthcare Records System. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        return html
    
    async def _send_sms_notification(
        self,
        record: Dict[str, Any],
        patient: Dict[str, Any],
        doctor: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send SMS notification"""
        
        doctor_name = doctor.get("displayName", "Your Doctor")
        record_type = record.get("fileType", "medical record").title()
        
        sms_body = f"""
📋 New {record_type} Available

From: {doctor_name}
Date: {self._format_date(record.get("uploadedAt"))}

View at: {settings.BASE_APP_URL}/patient

- Healthcare Records
""".strip()
        
        return await self.sms_provider.send(
            to=patient["phone"],
            subject="New Medical Record",
            body=sms_body
        )
    
    async def _create_notification_record(
        self,
        record: Dict[str, Any],
        patient: Dict[str, Any],
        doctor: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """Store notification in Firestore"""
        try:
            notification_data = {
                "type": "new_record",
                "userId": patient["uid"],
                "recordId": record.get("id"),
                "doctorId": doctor["uid"],
                "doctorName": doctor.get("displayName", doctor.get("email")),
                "recordType": record.get("fileType"),
                "fileName": record.get("fileName"),
                "message": f"New {record.get('fileType', 'record')} uploaded by {doctor.get('displayName', 'your doctor')}",
                "read": False,
                "channels": {
                    "email": results.get("email", {}).get("success", False),
                    "sms": results.get("sms", {}).get("success", False)
                },
                "createdAt": datetime.utcnow(),
                "metadata": {
                    "emailId": results.get("email", {}).get("messageId"),
                    "smsId": results.get("sms", {}).get("messageId")
                }
            }
            
            # Store in Firestore
            await self.db.collection("notifications").add(notification_data)
            logger.info(f"✅ Notification record created for patient {patient['uid']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create notification record: {str(e)}")
    
    def _format_date(self, timestamp) -> str:
        """Format timestamp to readable date"""
        try:
            if hasattr(timestamp, 'seconds'):
                dt = datetime.fromtimestamp(timestamp.seconds)
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                return str(timestamp)
            
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            return "Recently"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        patient_name: str = "User"
    ) -> Dict[str, Any]:
        """
        Send a simple email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            patient_name: Patient name for logging
            
        Returns:
            Dict with success status and message
        """
        try:
            result = await self.email_provider.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                from_name="E-Booklet"
            )
            return {"success": True, "message": "Email sent successfully"}
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def send_sms(
        self,
        to_phone: str,
        message: str,
        patient_name: str = "User"
    ) -> Dict[str, Any]:
        """
        Send a simple SMS notification
        
        Args:
            to_phone: Recipient phone number
            message: SMS message text
            patient_name: Patient name for logging
            
        Returns:
            Dict with success status and message
        """
        if not self.sms_provider:
            return {"success": False, "message": "SMS not configured. Please set TWILIO credentials in .env"}
        
        try:
            result = await self.sms_provider.send(
                to=to_phone,
                subject="Notification",
                body=message
            )
            if result.get("success"):
                return {"success": True, "message": "SMS sent successfully"}
            else:
                return {"success": False, "message": result.get("error", "SMS send failed")}
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
            return {"success": False, "message": str(e)}