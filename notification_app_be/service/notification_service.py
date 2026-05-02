"""
Notification Service
Business logic for notification operations
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from logging_middleware import LoggerService
from ..repository import NotificationRepository
import heapq
from enum import IntEnum


class NotificationType(IntEnum):
    """Priority weights for notification types"""
    EVENT = 1
    RESULT = 2
    PLACEMENT = 3


class NotificationService:
    """
    Service layer for notification operations.
    Handles business logic including filtering, sorting, and priority ranking.
    """

    def __init__(self, logger_service: LoggerService, db: Session):
        self.logger = logger_service
        self.db = db
        self.repository = NotificationRepository(db, logger_service)

    def _log(self, level: str, message: str, context: Optional[Dict] = None):
        """Log via middleware"""
        method = getattr(self.logger, level, self.logger.info)
        method(
            stack="backend",
            package="service",
            message=message,
            context=context or {}
        )

    async def fetch_notifications(
        self,
        student_id: str,
        page: int = 1,
        limit: int = 20,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None
    ) -> Dict:
        """
        Fetch paginated notifications with optional filtering
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

        # Calculate offset
        offset = (page - 1) * limit

        # Fetch from repository
        notifications = await self.repository.get_notifications(
            student_id=student_id,
            limit=limit,
            offset=offset,
            notification_type=notification_type,
            is_read=is_read
        )

        # Get total count
        total_count = await self.repository.count_notifications(
            student_id=student_id,
            notification_type=notification_type,
            is_read=is_read
        )

        return {
            "data": notifications,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "hasMore": offset + limit < total_count
            }
        }

    async def mark_notification_read(
        self,
        notification_id: str,
        student_id: str
    ) -> Dict:
        """
        Mark a single notification as read
        """
        self._log(
            "info",
            f"Marking notification {notification_id} as read"
        )

        result = await self.repository.update_notification_read_status(
            notification_id=notification_id,
            student_id=student_id,
            is_read=True
        )

        return result

    async def mark_all_read(self, student_id: str) -> int:
        """
        Mark all unread notifications as read
        """
        self._log("info", f"Marking all notifications as read for {student_id}")

        updated_count = await self.repository.update_all_notifications_read(
            student_id=student_id
        )

        self._log(
            "info",
            f"Updated {updated_count} notifications to read"
        )

        return updated_count

    async def delete_notification(self, notification_id: str, student_id: str):
        """
        Delete a notification
        """
        self._log(
            "info",
            f"Deleting notification {notification_id}"
        )

        await self.repository.delete_notification(notification_id, student_id)

    async def get_unread_counts(self, student_id: str) -> Dict:
        """
        Get count of unread notifications by type
        """
        self._log("info", f"Fetching unread count for {student_id}")

        counts = await self.repository.get_unread_count_by_type(student_id)

        return {
            "total": sum(counts.values()),
            "by_type": counts
        }

    async def get_priority_notifications(
        self,
        student_id: str,
        n: int = 10
    ) -> List[Dict]:
        """
        Get top N notifications by priority using min-heap
        
        Priority = (type_weight × 1000) + recency_score
        - Placement = highest priority
        - Recency decays over time
        """
        self._log(
            "info",
            f"Fetching top {n} priority notifications for {student_id}"
        )

        # Fetch all notifications
        all_notifications = await self.repository.get_all_notifications(student_id)

        # Score each notification
        scored_notifs = []
        for notif in all_notifications:
            score = self._calculate_priority_score(notif)
            # Store as negative for min-heap (to make max-heap)
            heapq.heappush(scored_notifs, (-score, notif))

        # Get top N
        top_n = []
        for _ in range(min(n, len(scored_notifs))):
            if scored_notifs:
                score, notif = heapq.heappop(scored_notifs)
                notif["priority_score"] = -score
                notif["priority_level"] = self._get_priority_level(-score)
                top_n.append(notif)

        self._log(
            "info",
            f"Selected top {len(top_n)} priority notifications"
        )

        return top_n

    def _calculate_priority_score(self, notification: Dict) -> float:
        """
        Calculate priority score for a notification
        
        Formula: (type_weight × 1000) + recency_factor
        """
        # Type weight
        notif_type = notification.get("type", "Event")
        type_weight = NotificationType[notif_type.upper()].value

        # Recency score (0-1000, higher for newer)
        timestamp = notification.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        
        age_hours = (datetime.utcnow() - timestamp).total_seconds() / 3600
        recency_score = max(0, 1000 - (age_hours * 10))

        # Combined priority
        priority_score = (type_weight * 1000) + recency_score

        return priority_score

    def _get_priority_level(self, score: float) -> str:
        """Get human-readable priority level"""
        if score >= 4000:
            return "Critical"
        elif score >= 3000:
            return "High"
        elif score >= 2000:
            return "Medium"
        else:
            return "Low"
