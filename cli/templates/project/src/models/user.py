"""User model for starter todo-app."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

# Note: In generated projects, RestEndpoint will be available from pylight package
# from pylight import RestEndpoint
# For now, using placeholder - will be replaced during template processing
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RestEndpoint(Base):
    __abstract__ = True


class User(RestEndpoint):
    """User model with authentication and role information."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="assignee")

