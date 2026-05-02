"""
Bulk Notifications API
Handles large-scale notification distribution
"""

from fastapi import APIRouter, BackgroundTasks
from typing import List, Dict
from logging_middleware import LoggerService
from sqlalchemy.orm import Session
from .service.notification_service import NotificationService
import asyncio
import uuid
from datetime import datetime

bulk_router = APIRouter(prefix="/api/notifications/bulk", tags=["bulk-notifications"])


async def process_bulk_notifications(
    notifications: List[Dict],
    logger_service: LoggerService,
    service: NotificationService
):
    """Process bulk notifications with async batch processing"""
    batch_size = 100
    success_count = 0
    error_count = 0
    
    for i in range(0, len(notifications), batch_size):
        batch = notifications[i:i + batch_size]
        batch_id = str(uuid.uuid4())
        
        logger_service.info(
            stack="backend",
            package="bulk_handler",
            message=f"Processing batch {batch_id}",
            context={"batch_index": i // batch_size + 1, "batch_size": len(batch)}
        )
        
        try:
            # Process each notification in batch
            for notif in batch:
                try:
                    # Create notification via repository
                    await service.repository.create_notification({
                        "id": str(uuid.uuid4()),
                        "student_id": notif.get("student_id", "default_student"),
                        "type": notif.get("type", "EVENT"),
                        "message": notif.get("message", ""),
                        "priority": notif.get("priority", "medium"),
                        "timestamp": datetime.utcnow()
                    })
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger_service.error(
                        stack="backend",
                        package="bulk_handler",
                        message=f"Error creating notification: {str(e)}",
                        context={"notification": notif}
                    )
            
            # Small delay between batches to avoid overwhelming database
            await asyncio.sleep(0.1)
        except Exception as e:
            logger_service.error(
                stack="backend",
                package="bulk_handler",
                message=f"Error processing batch: {str(e)}",
                context={"batch_id": batch_id}
            )
    
    logger_service.info(
        stack="backend",
        package="bulk_handler",
        message=f"Bulk processing complete",
        context={
            "total": len(notifications),
            "success": success_count,
            "errors": error_count,
            "success_rate": f"{(success_count / len(notifications) * 100):.1f}%" if notifications else "0%"
        }
    )


def create_bulk_router(logger_service: LoggerService, db: Session) -> APIRouter:
    """Create bulk notification routes"""
    
    service = NotificationService(logger_service, db)
    
    @bulk_router.post("/send")
    async def send_bulk_notifications(
        notifications: List[Dict],
        background_tasks: BackgroundTasks
    ):
        """
        Send notifications to multiple students asynchronously.
        Stage 5 Implementation: Bulk Notifications with async batch processing
        """
        logger_service.info(
            stack="backend",
            package="bulk_handler",
            message=f"Received bulk notification request for {len(notifications)} notifications",
            context={"count": len(notifications)}
        )
        
        # Process in background
        background_tasks.add_task(
            process_bulk_notifications,
            notifications,
            logger_service,
            service
        )
        
        return {
            "success": True,
            "message": f"Processing {len(notifications)} notifications",
            "count": len(notifications)
        }
    
    return bulk_router
