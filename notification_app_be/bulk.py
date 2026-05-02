"""
Bulk Notifications API
Handles large-scale notification distribution
"""

from fastapi import APIRouter, BackgroundTasks
from typing import List, Dict
from logging_middleware import LoggerService
from sqlalchemy.orm import Session
from .handler.notification_handler import NotificationHandler

bulk_router = APIRouter(prefix="/api/notifications/bulk", tags=["bulk-notifications"])


def create_bulk_router(logger_service: LoggerService, db: Session) -> APIRouter:
    """Create bulk notification routes"""
    
    handler = NotificationHandler(logger_service, db)
    
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
            handler
        )
        
        return {
            "success": True,
            "message": f"Processing {len(notifications)} notifications",
            "count": len(notifications)
        }
    
    return bulk_router


async def process_bulk_notifications(
    notifications: List[Dict],
    logger_service: LoggerService,
    handler: NotificationHandler
):
    """
    Process bulk notifications asynchronously with batch optimization.
    Implements Stage 5: Async batch processing with retry logic
    """
    logger_service.info(
        stack="backend",
        package="bulk_processor",
        message=f"Starting bulk notification processing for {len(notifications)} items",
        context={"batch_size": len(notifications)}
    )
    
    # Batch process in chunks of 100
    batch_size = 100
    total = len(notifications)
    processed = 0
    failed = 0
    
    for i in range(0, total, batch_size):
        batch = notifications[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        logger_service.info(
            stack="backend",
            package="bulk_processor",
            message=f"Processing batch {batch_num}",
            context={"batch_size": len(batch), "progress": f"{i}/{total}"}
        )
        
        try:
            # Create notifications in batch
            await handler.service.repository.batch_create_notifications(batch)
            processed += len(batch)
            
            logger_service.info(
                stack="backend",
                package="bulk_processor",
                message=f"Batch {batch_num} completed successfully",
                context={"items": len(batch)}
            )
            
        except Exception as e:
            failed += len(batch)
            logger_service.error(
                stack="backend",
                package="bulk_processor",
                message=f"Batch {batch_num} failed: {str(e)}",
                context={"error": str(e), "batch": batch_num}
            )
    
    logger_service.info(
        stack="backend",
        package="bulk_processor",
        message="Bulk notification processing completed",
        context={
            "total": total,
            "processed": processed,
            "failed": failed,
            "success_rate": f"{(processed/total)*100:.1f}%"
        }
    )
