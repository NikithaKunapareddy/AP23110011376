"""
Notification Handler
Orchestrates notification API requests and responses
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from logging_middleware import LoggerService
from ..service import NotificationService


class NotificationHandler:
    """Handles notification-related HTTP requests"""

    def __init__(self, logger_service: LoggerService, db: Session):
        self.logger = logger_service
        self.db = db
        self.service = NotificationService(logger_service, db)

    def _log(self, level: str, message: str, context: Optional[Dict] = None):
        """Log via middleware"""
        method = getattr(self.logger, level, self.logger.info)
        method(
            stack="backend",
            package="handler",
            message=message,
            context=context or {}
        )

    async def get_notifications(
        self,
        student_id: str,
        page: int = 1,
        limit: int = 20,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None
    ) -> Dict:
        """
        Fetch paginated notifications for a student
        """
        self._log(
            "info",
            f"Fetching notifications for student {student_id}",
            context={
                "page": page,
                "limit": limit,
                "type": notification_type,
                "is_read": is_read
            }
        )

        try:
            notifications = await self.service.fetch_notifications(
                student_id=student_id,
                page=page,
                limit=limit,
                notification_type=notification_type,
                is_read=is_read
            )

            return {
                "success": True,
                "data": notifications["data"],
                "pagination": notifications["pagination"]
            }
        
        except Exception as e:
            self._log("error", f"Error fetching notifications: {str(e)}")
            raise

    async def mark_as_read(self, notification_id: str, student_id: str) -> Dict:
        """
        Mark a notification as read
        """
        self._log(
            "info",
            f"Marking notification {notification_id} as read"
        )

        try:
            result = await self.service.mark_notification_read(
                notification_id=notification_id,
                student_id=student_id
            )
            
            return {
                "success": True,
                "message": "Notification marked as read",
                "data": result
            }
        
        except Exception as e:
            self._log("error", f"Error marking notification as read: {str(e)}")
            raise

    async def mark_all_as_read(self, student_id: str) -> Dict:
        """
        Mark all notifications as read
        """
        self._log("info", f"Marking all notifications as read for student {student_id}")

        try:
            updated_count = await self.service.mark_all_read(student_id)
            
            return {
                "success": True,
                "message": "All notifications marked as read",
                "updatedCount": updated_count
            }
        
        except Exception as e:
            self._log("error", f"Error marking all notifications as read: {str(e)}")
            raise

    async def delete_notification(self, notification_id: str, student_id: str) -> Dict:
        """
        Delete a notification
        """
        self._log(
            "info",
            f"Deleting notification {notification_id}",
            context={"student_id": student_id}
        )

        try:
            await self.service.delete_notification(notification_id, student_id)
            
            return {
                "success": True,
                "message": "Notification deleted successfully"
            }
        
        except Exception as e:
            self._log("error", f"Error deleting notification: {str(e)}")
            raise

    async def get_unread_count(self, student_id: str) -> Dict:
        """
        Get count of unread notifications
        """
        self._log("info", f"Fetching unread count for student {student_id}")

        try:
            counts = await self.service.get_unread_counts(student_id)
            
            return {
                "success": True,
                "unreadCount": counts["total"],
                "byType": counts["by_type"]
            }
        
        except Exception as e:
            self._log("error", f"Error fetching unread count: {str(e)}")
            raise

    async def get_priority_inbox(self, student_id: str, n: int = 10) -> Dict:
        """
        Get top N priority notifications
        """
        self._log(
            "info",
            f"Fetching priority inbox for student {student_id}",
            context={"top_n": n}
        )

        try:
            priority_notifs = await self.service.get_priority_notifications(
                student_id=student_id,
                n=n
            )
            
            return {
                "success": True,
                "topN": n,
                "priorityInbox": priority_notifs
            }
        
        except Exception as e:
            self._log("error", f"Error fetching priority inbox: {str(e)}")
            raise
