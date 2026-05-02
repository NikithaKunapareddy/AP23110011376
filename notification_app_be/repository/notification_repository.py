"""
Notification Repository
Data access layer for notification operations using SQLAlchemy
"""

from typing import List, Dict, Optional
from logging_middleware import LoggerService
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Notification, NotificationType


class NotificationRepository:
    """Repository for notification data access using SQLAlchemy"""
    
    def __init__(self, db: Session, logger_service: LoggerService):
        self.db = db
        self.logger = logger_service

    def _log(self, level: str, message: str, context: Optional[Dict] = None):
        """Log via middleware"""
        method = getattr(self.logger, level, self.logger.info)
        method(
            stack="backend",
            package="repository",
            message=message,
            context=context or {}
        )

    async def get_notifications(
        self,
        student_id: str,
        limit: int = 20,
        offset: int = 0,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None
    ) -> List[Dict]:
        """Fetch paginated notifications for a student"""
        self._log(
            "info",
            f"Fetching notifications from repository",
            context={"student_id": student_id, "limit": limit, "offset": offset}
        )

        query = self.db.query(Notification).filter(
            Notification.student_id == student_id
        )
        
        if notification_type:
            query = query.filter(Notification.type == notification_type)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        notifications = query.order_by(Notification.timestamp.desc()).offset(offset).limit(limit).all()
        
        return [n.to_dict() for n in notifications]

    async def count_notifications(
        self,
        student_id: str,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None
    ) -> int:
        """Count notifications matching criteria"""
        self._log("info", f"Counting notifications for {student_id}")
        
        query = self.db.query(Notification).filter(
            Notification.student_id == student_id
        )
        
        if notification_type:
            query = query.filter(Notification.type == notification_type)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        return query.count()

    async def get_all_notifications(self, student_id: str) -> List[Dict]:
        """Fetch all notifications for priority ranking"""
        self._log("info", f"Fetching all notifications for {student_id}")

        notifications = self.db.query(Notification).filter(
            Notification.student_id == student_id
        ).all()
        
        return [n.to_dict() for n in notifications]

    async def update_notification_read_status(
        self,
        notification_id: str,
        student_id: str,
        is_read: bool
    ) -> Dict:
        """Update notification read status"""
        self._log(
            "info",
            f"Updating notification {notification_id} read status to {is_read}"
        )

        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.student_id == student_id
        ).first()
        
        if notification:
            notification.is_read = is_read
            self.db.commit()
            return notification.to_dict()
        
        return {}

    async def update_all_notifications_read(self, student_id: str) -> int:
        """Mark all unread notifications as read"""
        self._log("info", f"Marking all notifications as read for {student_id}")

        count = self.db.query(Notification).filter(
            Notification.student_id == student_id,
            Notification.is_read == False
        ).update({Notification.is_read: True})
        
        self.db.commit()
        return count

    async def delete_notification(
        self,
        notification_id: str,
        student_id: str
    ):
        """Delete a notification"""
        self._log(
            "info",
            f"Deleting notification {notification_id} for student {student_id}"
        )

        self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.student_id == student_id
        ).delete()
        
        self.db.commit()

    async def get_unread_count_by_type(self, student_id: str) -> Dict:
        """Get unread notification count grouped by type"""
        self._log("info", f"Fetching unread count by type for {student_id}")

        results = self.db.query(
            Notification.type,
            func.count(Notification.id)
        ).filter(
            Notification.student_id == student_id,
            Notification.is_read == False
        ).group_by(Notification.type).all()
        
        return {type_name: count for type_name, count in results}

    async def create_notification(self, notification: Dict) -> Dict:
        """Create a new notification"""
        self._log(
            "info",
            f"Creating notification",
            context={"type": notification.get("type")}
        )

        import uuid
        new_notification = Notification(
            id=str(uuid.uuid4()),
            student_id=notification.get("student_id", "default"),
            type=notification.get("type"),
            message=notification.get("message"),
            timestamp=datetime.utcnow(),
            is_read=notification.get("is_read", False),
            priority=notification.get("priority", "medium")
        )
        
        self.db.add(new_notification)
        self.db.commit()
        self.db.refresh(new_notification)
        
        return new_notification.to_dict()

    async def batch_create_notifications(
        self,
        notifications: List[Dict]
    ) -> int:
        """Create multiple notifications (for bulk operations)"""
        self._log(
            "info",
            f"Creating {len(notifications)} notifications in batch"
        )

        import uuid
        new_notifications = [
            Notification(
                id=str(uuid.uuid4()),
                student_id=n.get("student_id", "default"),
                type=n.get("type"),
                message=n.get("message"),
                timestamp=datetime.utcnow(),
                is_read=n.get("is_read", False),
                priority=n.get("priority", "medium")
            )
            for n in notifications
        ]
        
        self.db.add_all(new_notifications)
        self.db.commit()
        
        return len(new_notifications)
