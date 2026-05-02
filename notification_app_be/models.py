"""
SQLAlchemy Models for Notifications
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()


class NotificationType(str, PyEnum):
    """Notification types"""
    PLACEMENT = "Placement"
    RESULT = "Result"
    EVENT = "Event"


class Notification(Base):
    """Notification model with optimized indexes"""
    __tablename__ = "notifications"
    __table_args__ = (
        # Composite index for common query patterns
        Index('idx_student_read_created', 'student_id', 'is_read', 'timestamp'),
        # Index for type filtering
        Index('idx_student_type', 'student_id', 'type'),
        # Index for pagination
        Index('idx_student_created', 'student_id', 'timestamp'),
    )
    
    id = Column(String, primary_key=True, unique=True)
    student_id = Column(String, nullable=False, index=True)  # Single-column index
    type = Column(String, nullable=False, index=True)        # Single-column index
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)  # For ordering
    is_read = Column(Boolean, default=False, index=True)     # For filtering
    priority = Column(String, default="medium")
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() + "Z",
            "isRead": self.is_read,
            "priority": self.priority
        }


# Database configuration
DATABASE_URL = "sqlite:///./afford.db"
# For PostgreSQL, use: DATABASE_URL = "postgresql://afford_user:afford_pass@localhost:5432/afford_db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
