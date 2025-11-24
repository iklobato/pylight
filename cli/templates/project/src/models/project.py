"""Project model for starter todo-app."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Note: In generated projects, RestEndpoint will be available from pylight package
# from pylight import RestEndpoint
# For now, using placeholder - will be replaced during template processing
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RestEndpoint(Base):
    __abstract__ = True


class Project(RestEndpoint):
    """Project model that contains multiple tasks."""

    __tablename__ = "project"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", backref="projects")
    tasks = relationship("Task", back_populates="project")

