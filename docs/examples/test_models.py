"""Test models for integration examples."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.domain.entities.rest_endpoint import RestEndpoint


class Product(RestEndpoint):
    """Product model for testing REST, GraphQL, and WebSocket features."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(RestEndpoint):
    """User model for testing authentication features."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

