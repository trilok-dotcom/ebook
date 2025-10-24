import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Base class for notification providers"""
    
    @abstractmethod
    async def send(self, to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """Send notification"""
        pass


class EmailProvider(NotificationProvider):
    """Email notification provider using Gmail SMTP"""
    
    def __init__(self):
        self.provider_type = "smtp"  # Always use SMTP for Gmail
        self._validate_config()
    
    def _validate_config(self):
        """Validate SMTP configuration"""
        required = {
            'SMTP_HOST': settings.SMTP_HOST,
            'SMTP_PORT': settings.SMTP_PORT,
            'SMTP_USERNAME': settings.SMTP_USERNAME,
            'SMTP_PASSWORD': settings.SMTP_PASSWORD,
            'SMTP_FROM_EMAIL': settings.SMTP_FROM_EMAIL,
        }
        
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing SMTP configuration: {', '.join(missing)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send(self, to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """Send email notification via Gmail SMTP"""
        try:
            # Run SMTP in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._send_smtp_sync, 
                to, 
                subject, 
                body
            )
            return result
        except Exception as e:
            logger.error(f"Email send failed to {to}: {str(e)}")
            raise
    
    def _send_smtp_sync(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Synchronous SMTP send (runs in thread pool)"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = to
        msg['Subject'] = subject
        
        # Attach plain text and HTML versions
        msg.attach(MIMEText(body, 'plain'))
        
        # If HTML body is provided in kwargs
        if 'html_body' in body or '<html>' in body.lower():
            msg.attach(MIMEText(body, 'html'))
        
        # Send email
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                server.set_debuglevel(0)  # Set to 1 for debugging
                
                if settings.SMTP_USE_TLS:
                    server.starttls()
                
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            message_id = f"smtp-{abs(hash(to + subject + str(asyncio.get_event_loop().time())))}"
            
            logger.info(f"✅ Email sent successfully to {to}")
            
            return {
                "success": True,
                "messageId": message_id,
                "provider": "gmail-smtp",
                "recipient": to
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed. Check your Gmail App Password: {str(e)}")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error occurred: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {str(e)}")
            raise


class SMSProvider(NotificationProvider):
    """SMS notification provider using Twilio (Optional)"""
    
    def __init__(self):
        self._client = None
        self._validate_config()
    
    def _validate_config(self):
        """Validate Twilio configuration"""
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM_NUMBER]):
            logger.warning("⚠️  Twilio SMS is not configured. SMS notifications will be skipped.")
    
    def _get_client(self):
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
            except ImportError:
                logger.error("Twilio package not installed. Run: pip install twilio")
                raise
        return self._client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send(self, to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """Send SMS notification via Twilio"""
        try:
            # Check if configuration is available
            if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM_NUMBER]):
                logger.warning(f"⚠️  SMS skipped for {to}: Twilio not configured")
                return {
                    "success": False,
                    "messageId": None,
                    "provider": "twilio",
                    "error": "SMS not configured"
                }
            
            client = self._get_client()
            
            # Run Twilio API call in thread pool
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    from_=settings.TWILIO_FROM_NUMBER,
                    to=to,
                    body=body
                )
            )
            
            logger.info(f"✅ SMS sent successfully to {to}: {message.sid}")
            
            return {
                "success": True,
                "messageId": message.sid,
                "provider": "twilio",
                "recipient": to
            }
            
        except Exception as e:
            logger.error(f"❌ SMS send failed to {to}: {str(e)}")
            return {
                "success": False,
                "messageId": None,
                "provider": "twilio",
                "error": str(e)
            }