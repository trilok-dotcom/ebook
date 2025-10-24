import os
import json
from typing import List, Literal
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    # Server
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(default="development")
    
    # CORS
    ALLOWED_ORIGINS: str = Field(default="http://localhost:5173")
    
    # Firebase
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = Field(default=None)
    FIREBASE_SERVICE_ACCOUNT_PATH: str | None = Field(default=None)
    FIREBASE_PROJECT_ID: str
    
    # Application
    BASE_APP_URL: str = Field(default="http://localhost:5173")
    
    # Notifications
    NOTIFY_CHANNELS: str = Field(default="email")
    NOTIFY_RETRY_ATTEMPTS: int = Field(default=3)
    NOTIFY_TIMEOUT_SECONDS: int = Field(default=30)
    
    # Email
    EMAIL_PROVIDER: Literal["sendgrid", "smtp"] = Field(default="sendgrid")
    SENDGRID_API_KEY: str | None = Field(default=None)
    SENDGRID_FROM_EMAIL: str | None = Field(default=None)
    SENDGRID_FROM_NAME: str = Field(default="Healthcare App")
    
    # SMTP
    SMTP_HOST: str | None = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USE_TLS: bool = Field(default=True)
    SMTP_USERNAME: str | None = Field(default=None)
    SMTP_PASSWORD: str | None = Field(default=None)
    SMTP_FROM_EMAIL: str | None = Field(default=None)
    SMTP_FROM_NAME: str = Field(default="Healthcare App")
    
    # SMS
    TWILIO_ACCOUNT_SID: str | None = Field(default=None)
    TWILIO_AUTH_TOKEN: str | None = Field(default=None)
    TWILIO_FROM_NUMBER: str | None = Field(default=None)
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    LOG_FORMAT: Literal["json", "text"] = Field(default="json")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    
    # File Upload
    MAX_FILE_SIZE_MB: int = Field(default=10)
    ALLOWED_FILE_TYPES: str = Field(default="pdf,jpg,jpeg,png,dcm")
    
    @validator("ALLOWED_ORIGINS")
    def parse_origins(cls, v):
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    
    @validator("NOTIFY_CHANNELS")
    def parse_channels(cls, v):
        channels = [ch.strip().lower() for ch in v.split(",") if ch.strip()]
        valid = {"email", "sms", "push"}
        for ch in channels:
            if ch not in valid:
                raise ValueError(f"Invalid notification channel: {ch}. Must be one of {valid}")
        return channels
    
    @validator("ALLOWED_FILE_TYPES")
    def parse_file_types(cls, v):
        return [ft.strip().lower() for ft in v.split(",") if ft.strip()]
    
    def validate_notification_config(self):
        """Validate notification provider configuration"""
        errors = []
        
        if "email" in self.NOTIFY_CHANNELS:
            if self.EMAIL_PROVIDER == "sendgrid":
                if not self.SENDGRID_API_KEY:
                    errors.append("SENDGRID_API_KEY is required for email notifications")
                if not self.SENDGRID_FROM_EMAIL:
                    errors.append("SENDGRID_FROM_EMAIL is required for email notifications")
            elif self.EMAIL_PROVIDER == "smtp":
                if not all([self.SMTP_HOST, self.SMTP_USERNAME, self.SMTP_PASSWORD, self.SMTP_FROM_EMAIL]):
                    errors.append("SMTP configuration incomplete (HOST, USERNAME, PASSWORD, FROM_EMAIL required)")
        
        if "sms" in self.NOTIFY_CHANNELS:
            if not all([self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN, self.TWILIO_FROM_NUMBER]):
                errors.append("Twilio configuration incomplete (ACCOUNT_SID, AUTH_TOKEN, FROM_NUMBER required)")
        
        return errors
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()