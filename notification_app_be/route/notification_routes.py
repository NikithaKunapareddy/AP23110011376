"""
Notification Routes
FastAPI route definitions for notification endpoints
"""

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
from sqlalchemy.orm import Session
from logging_middleware import LoggerService
from ..handler import NotificationHandler

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def create_notification_router(logger_service: LoggerService, db: Session) -> APIRouter:
    """Factory function to create router with dependency injection"""
    
    handler = NotificationHandler(logger_service, db)

    @router.get("/")
    async def get_notifications(
        request: Request,
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        type: Optional[str] = Query(None),
        isRead: Optional[bool] = Query(None)
    ):
        """
        Fetch paginated notifications for logged-in user
        
        Query Parameters:
        - page: Page number (default 1)
        - limit: Items per page (default 20, max 100)
        - type: Filter by type (Placement, Result, Event)
        - isRead: Filter by read status
        """
        # Use default student_id if not in auth context
        student_id = getattr(request.state, 'student_id', 'default_student')
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')
        
        logger_service.info(
            stack="backend",
            package="route",
            message=f"GET /api/notifications",
            correlation_id=correlation_id,
            context={"page": page, "limit": limit}
        )

        try:
            result = await handler.get_notifications(
                student_id=student_id,
                page=page,
                limit=limit,
                notification_type=type,
                is_read=isRead
            )
            
            logger_service.info(
                stack="backend",
                package="route",
                message="Notifications fetched successfully",
                correlation_id=correlation_id
            )
            
            return result
        
        except Exception as e:
            logger_service.error(
                stack="backend",
                package="route",
                message=f"Error fetching notifications: {str(e)}",
                correlation_id=correlation_id
            )
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.put("/{notification_id}/read")
    async def mark_notification_read(
        request: Request,
        notification_id: str
    ):
        """Mark a specific notification as read"""
        student_id = getattr(request.state, 'student_id', 'default_student')
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')

        logger_service.info(
            stack="backend",
            package="route",
            message=f"PUT /api/notifications/{notification_id}/read",
            correlation_id=correlation_id
        )

        try:
            result = await handler.mark_as_read(
                notification_id=notification_id,
                student_id=student_id
            )
            
            return result
        
        except Exception as e:
            logger_service.error(
                stack="backend",
                package="route",
                message=f"Error marking notification as read: {str(e)}",
                correlation_id=correlation_id
            )
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.put("/read-all")
    async def mark_all_read(request: Request):
        """Mark all notifications as read"""
        student_id = getattr(request.state, 'student_id', 'default_student')
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')

        logger_service.info(
            stack="backend",
            package="route",
            message="PUT /api/notifications/read-all",
            correlation_id=correlation_id
        )

        try:
            result = await handler.mark_all_as_read(student_id=student_id)
            return result
        
        except Exception as e:
            logger_service.error(
                stack="backend",
                package="route",
                message=f"Error marking all notifications as read: {str(e)}",
                correlation_id=correlation_id
            )
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.delete("/{notification_id}")
    async def delete_notification(
        request: Request,
        notification_id: str
    ):
        """Delete a notification"""
        student_id = getattr(request.state, 'student_id', 'default_student')
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')

        logger_service.info(
            stack="backend",
            package="route",
            message=f"DELETE /api/notifications/{notification_id}",
            correlation_id=correlation_id
        )

        try:
            await handler.delete_notification(
                notification_id=notification_id,
                student_id=student_id
            )
            
            return {"success": True}
        
        except Exception as e:
            logger_service.error(
                stack="backend",
                package="route",
                message=f"Error deleting notification: {str(e)}",
                correlation_id=correlation_id
            )
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.get("/unread/count")
    async def get_unread_count(request: Request):
        """Get unread notification counts by type"""
        student_id = getattr(request.state, 'student_id', 'default_student')
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')

        logger_service.info(
            stack="backend",
            package="route",
            message="GET /api/notifications/unread/count",
            correlation_id=correlation_id
        )

        try:
            result = await handler.get_unread_count(student_id=student_id)
            return result
        
        except Exception as e:
            logger_service.error(
                stack="backend",
                package="route",
                message=f"Error fetching unread count: {str(e)}",
                correlation_id=correlation_id
            )
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @router.get("/priority/inbox")
    async def get_priority_inbox(
        request: Request,
        n: int = Query(10, ge=1, le=50)
    ):
        """Get top N priority notifications"""
        student_id = getattr(request.state, 'student_id', 'default_student')
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')

        logger_service.info(
            stack="backend",
            package="route",
            message=f"GET /api/notifications/priority/inbox?n={n}",
            correlation_id=correlation_id
        )

        try:
            result = await handler.get_priority_inbox(
                student_id=student_id,
                n=n
            )
            return result
        
        except Exception as e:
            logger_service.error(
                stack="backend",
                package="route",
                message=f"Error fetching priority inbox: {str(e)}",
                correlation_id=correlation_id
            )
            raise HTTPException(status_code=500, detail="Internal Server Error")

    return router
