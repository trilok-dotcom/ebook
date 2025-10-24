import logging
from typing import Optional, Dict, List
from datetime import datetime
from firebase_admin import firestore
from .models import UserRole, RecordStatus

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for Firestore operations"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
    
    # User operations
    async def get_user(self, uid: str) -> Optional[Dict]:
        """Get user by UID"""
        try:
            doc = self.db.collection("users").document(uid).get()
            if doc.exists:
                return {"uid": uid, **doc.to_dict()}
            return None
        except Exception as e:
            logger.error(f"Error fetching user {uid}: {str(e)}")
            raise
    
    async def create_user(self, uid: str, user_data: Dict) -> Dict:
        """Create new user"""
        try:
            user_ref = self.db.collection("users").document(uid)
            
            data = {
                **user_data,
                "uid": uid,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "isActive": True
            }
            
            user_ref.set(data)
            logger.info(f"User created: {uid}")
            return data
        except Exception as e:
            logger.error(f"Error creating user {uid}: {str(e)}")
            raise
    
    async def update_user(self, uid: str, updates: Dict) -> Dict:
        """Update user"""
        try:
            user_ref = self.db.collection("users").document(uid)
            updates["updatedAt"] = firestore.SERVER_TIMESTAMP
            user_ref.update(updates)
            logger.info(f"User updated: {uid}")
            return await self.get_user(uid)
        except Exception as e:
            logger.error(f"Error updating user {uid}: {str(e)}")
            raise
    
    # Record operations
    async def get_record(self, record_id: str) -> Optional[Dict]:
        """Get record by ID"""
        try:
            doc = self.db.collection("records").document(record_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["recordId"] = record_id
                return data
            return None
        except Exception as e:
            logger.error(f"Error fetching record {record_id}: {str(e)}")
            raise
    
    async def create_record(self, record_data: Dict) -> Dict:
        """Create new record"""
        try:
            record_ref = self.db.collection("records").document()
            
            data = {
                **record_data,
                "recordId": record_ref.id,
                "uploadedAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "status": RecordStatus.ACTIVE.value,
                "viewedBy": [],
                "sharedWith": []
            }
            
            record_ref.set(data)
            logger.info(f"Record created: {record_ref.id}")
            return data
        except Exception as e:
            logger.error(f"Error creating record: {str(e)}")
            raise
    
    async def get_patient_records(
        self,
        patient_uid: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get all records for a patient"""
        try:
            query = (
                self.db.collection("records")
                .where("uploadedFor", "==", patient_uid)
                .where("status", "==", RecordStatus.ACTIVE.value)
                .order_by("uploadedAt", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset)
            )
            
            docs = query.stream()
            records = []
            for doc in docs:
                data = doc.to_dict()
                data["recordId"] = doc.id
                records.append(data)
            
            return records
        except Exception as e:
            logger.error(f"Error fetching patient records: {str(e)}")
            raise
    
    async def get_doctor_records(
        self,
        doctor_uid: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get all records uploaded by a doctor"""
        try:
            query = (
                self.db.collection("records")
                .where("uploadedBy", "==", doctor_uid)
                .where("status", "==", RecordStatus.ACTIVE.value)
                .order_by("uploadedAt", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset)
            )
            
            docs = query.stream()
            records = []
            for doc in docs:
                data = doc.to_dict()
                data["recordId"] = doc.id
                records.append(data)
            
            return records
        except Exception as e:
            logger.error(f"Error fetching doctor records: {str(e)}")
            raise
    
    async def mark_record_viewed(self, record_id: str, user_uid: str):
        """Mark record as viewed by user"""
        try:
            record_ref = self.db.collection("records").document(record_id)
            record_ref.update({
                "viewedBy": firestore.ArrayUnion([user_uid]),
                "viewedAt": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Record {record_id} marked as viewed by {user_uid}")
        except Exception as e:
            logger.error(f"Error marking record as viewed: {str(e)}")
            raise
    
    # Notification operations
    async def get_user_notifications(
        self,
        user_uid: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """Get notifications for a user"""
        try:
            query = self.db.collection("notifications").where("userId", "==", user_uid)
            
            if unread_only:
                query = query.where("isRead", "==", False)
            
            query = query.order_by("sentAt", direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            notifications = []
            for doc in docs:
                data = doc.to_dict()
                data["notificationId"] = doc.id
                notifications.append(data)
            
            return notifications
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            raise
    
    async def mark_notification_read(self, notification_id: str):
        """Mark notification as read"""
        try:
            notification_ref = self.db.collection("notifications").document(notification_id)
            notification_ref.update({
                "isRead": True,
                "readAt": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Notification {notification_id} marked as read")
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            raise
    
    # Audit log
    async def create_audit_log(self, log_data: Dict):
        """Create audit log entry"""
        try:
            log_ref = self.db.collection("audit_logs").document()
            data = {
                **log_data,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            log_ref.set(data)
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            # Don't raise - audit logging should not break the main flow
