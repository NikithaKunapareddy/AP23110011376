"""
Main FastAPI Application
Ties together logging middleware, notification system, and vehicle scheduler
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from logging_middleware import LoggerService, LoggingMiddleware
from notification_app_be.route import create_notification_router
from notification_app_be.bulk import create_bulk_router
from notification_app_be.models import init_db, get_db, SessionLocal
from vehicle_maintenance_scheduler import SchedulerHandler

# Initialize logger
logger_service = LoggerService(log_dir="logs", app_name="afford-app")

# Initialize database
init_db()
logger_service.info(
    stack="backend",
    package="main",
    message="Database initialized successfully"
)

# Create FastAPI app
app = FastAPI(
    title="Afford Medical - Backend Services",
    description="API for Vehicle Maintenance Scheduler & Campus Notifications",
    version="1.0.0"
)

# Add logging middleware
app.add_middleware(LoggingMiddleware, logger_service=logger_service)

# Get database session
db = SessionLocal()

# Register notification routes with database
notification_router = create_notification_router(logger_service, db)
app.include_router(notification_router)

# Register bulk notification routes
bulk_router = create_bulk_router(logger_service, db)
app.include_router(bulk_router)

# Credentials for API calls
CLIENT_ID = "7f1331dd-c33a-4e79-97e5-8d014932869a"
CLIENT_SECRET = "KbkdTVytDpmAmnUk"

# Initialize scheduler handler
scheduler_handler = SchedulerHandler(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    logger_service=logger_service
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "service": "Afford Medical Backend",
        "version": "1.0.0",
        "endpoints": {
            "notifications": "/api/notifications",
            "vehicle_scheduler": "/api/scheduler",
            "docs": "/docs"
        }
    }


@app.get("/api/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    logger_service.info(
        stack="backend",
        package="handler",
        message="Scheduler status check"
    )
    
    return {
        "status": "operational",
        "service": "Vehicle Maintenance Scheduler",
        "endpoints": {
            "schedule": "/api/scheduler/schedule",
            "depots": "/api/scheduler/depots",
            "vehicles": "/api/scheduler/vehicles"
        }
    }


@app.post("/api/scheduler/schedule")
async def run_vehicle_scheduling():
    """
    Run complete vehicle maintenance scheduling
    Fetches depots and vehicles from Afford APIs and optimizes scheduling
    """
    logger_service.info(
        stack="backend",
        package="handler",
        message="Starting vehicle maintenance scheduling"
    )

    try:
        result = await scheduler_handler.run_scheduling()
        
        logger_service.info(
            stack="backend",
            package="handler",
            message="Scheduling completed successfully"
        )
        
        return result
    
    except Exception as e:
        logger_service.error(
            stack="backend",
            package="handler",
            message=f"Scheduling failed: {str(e)}"
        )
        
        return JSONResponse(
            status_code=500,
            content={"error": "Scheduling failed", "details": str(e)}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "afford-backend"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging"""
    logger_service.error(
        stack="backend",
        package="middleware",
        message=f"Unhandled exception: {str(exc)}",
        context={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"}
    )


if __name__ == "__main__":
    logger_service.info(
        stack="backend",
        package="main",
        message="Starting Afford Medical Backend Server",
        context={"host": "0.0.0.0", "port": 8000}
    )
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Use our custom logging middleware
    )
