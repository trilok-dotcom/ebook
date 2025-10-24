from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"


class RecordStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class FileType(str, Enum):
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    SCAN = "scan"
    XRAY = "xray"
    OTHER = "other"


class NotificationType(str, Enum):
    RECORD_UPLOADED = "record_uploaded"
    APPOINTMENT_REMINDER = "appointment_reminder"
    MESSAGE = "message"


class NotificationStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"


# Request Models
class NotifyUploadRequest(BaseModel):
    recordId: str = Field(..., min_length=1, max_length=200)
    
    @validator('recordId')
    def validate_record_id(cls, v):
        if not v.strip():
            raise ValueError('recordId cannot be empty')
        return v.strip()


class CreateRecordRequest(BaseModel):
    uploadedFor: str = Field(..., description="Patient UID")
    fileType: FileType
    fileName: str
    fileUrl: str
    filePath: str
    fileSize: int = Field(..., gt=0)
    mimeType: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=1000)
    notes: Optional[str] = Field(default="", max_length=2000)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


# Response Models
class NotifyResult(BaseModel):
    status: Literal["success", "partial", "failed"]
    channels: List[str]
    notificationId: Optional[str] = None
    errors: Optional[Dict[str, str]] = None


class UserProfile(BaseModel):
    uid: str
    email: str
    displayName: Optional[str]
    role: UserRole
    phoneNumber: Optional[str] = None
    photoURL: Optional[str] = None
    specialization: Optional[str] = None
    preferences: Optional[Dict[str, bool]] = None


class RecordResponse(BaseModel):
    recordId: str
    uploadedBy: str
    uploadedFor: str
    fileType: FileType
    fileName: str
    fileUrl: str
    title: str
    description: str
    notes: str
    uploadedAt: datetime
    status: RecordStatus


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    environment: str
    version: str = "1.0.0"