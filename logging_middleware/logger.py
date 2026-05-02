"""
Centralized Logging Service
Structured JSON logging with file and console output
"""

import logging
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LoggerService:
    """Centralized logging service with structured JSON output"""
    
    def __init__(self, log_dir: str = "logs", app_name: str = "app"):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        log_file = self.log_dir / f"{app_name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter for file (JSON)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _get_timestamp(self) -> str:
        """Generate ISO format timestamp"""
        return datetime.now(timezone.utc).isoformat()
    
    def log(
        self,
        level: str,
        stack: str,
        package: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log a message with structured JSON format
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            stack: Stack identifier (backend, frontend, etc)
            package: Package/module name
            message: Log message
            context: Additional context data
            correlation_id: Request correlation ID
        """
        log_entry = {
            "logID": str(uuid.uuid4()),
            "timestamp": self._get_timestamp(),
            "stack": stack,
            "level": level,
            "package": package,
            "message": message,
            "context": context or {}
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_entry))
    
    def debug(
        self,
        stack: str,
        package: str,
        message: str,
        context: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        self.log("debug", stack, package, message, context, correlation_id)
    
    def info(
        self,
        stack: str,
        package: str,
        message: str,
        context: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        self.log("info", stack, package, message, context, correlation_id)
    
    def warning(
        self,
        stack: str,
        package: str,
        message: str,
        context: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        self.log("warning", stack, package, message, context, correlation_id)
    
    def error(
        self,
        stack: str,
        package: str,
        message: str,
        context: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        self.log("error", stack, package, message, context, correlation_id)
    
    def critical(
        self,
        stack: str,
        package: str,
        message: str,
        context: Optional[Dict] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        self.log("critical", stack, package, message, context, correlation_id)