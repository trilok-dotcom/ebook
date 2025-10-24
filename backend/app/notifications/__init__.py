"""
Notifications package for Healthcare Records System

Provides email and SMS notification services for patient notifications.
"""

from .service import NotificationService
from .providers import EmailProvider, SMSProvider

__all__ = ["NotificationService", "EmailProvider", "SMSProvider"]