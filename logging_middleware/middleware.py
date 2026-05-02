from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import time
import uuid
from .logger import LoggerService, LogLevel


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for comprehensive request/response logging.
    Adds correlation IDs and logs all HTTP traffic.
    """

    def __init__(self, app, logger_service: LoggerService):
        super().__init__(app)
        self.logger_service = logger_service

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with logging

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        # Log incoming request
        start_time = time.time()
        request_body = await self._get_request_body(request)

        self.logger_service.info(
            stack="backend",
            package="middleware",
            message=f"Incoming {request.method} {request.url.path}",
            correlation_id=correlation_id,
            context={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            self.logger_service.info(
                stack="backend",
                package="middleware",
                message=f"Response {request.method} {request.url.path} - Status {response.status_code}",
                correlation_id=correlation_id,
                context={
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2)
                }
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as e:
            process_time = time.time() - start_time
            self.logger_service.error(
                stack="backend",
                package="middleware",
                message=f"Error processing {request.method} {request.url.path}",
                correlation_id=correlation_id,
                context={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "process_time_ms": round(process_time * 1000, 2)
                }
            )
            raise

    async def _get_request_body(self, request: Request) -> dict:
        """Extract request body for logging"""
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    import json
                    return json.loads(body)
        except:
            pass
        return {}
