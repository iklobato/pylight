"""Task model for starter todo-app."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# Note: In generated projects, RestEndpoint will be available from pylight package
# from pylight import RestEndpoint
# For now, using placeholder - will be replaced during template processing
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RestEndpoint(Base):
    __abstract__ = True


class TaskStatus(enum.Enum):
    """Task status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(RestEndpoint):
    """Task model within a project."""

    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    assignee_id = Column(Integer, ForeignKey("user.id"))
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = Column(DateTime)

    assignee = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")

