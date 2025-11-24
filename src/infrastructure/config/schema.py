"""Configuration schema definitions."""

from typing import Optional
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str


class SwaggerConfig(BaseModel):
    """Swagger/OpenAPI configuration."""

    title: str
    version: str
    description: Optional[str] = ""


class AuthConfig(BaseModel):
    """Authentication configuration."""

    jwt_secret: str
    oauth2_enabled: bool = False


class CacheConfig(BaseModel):
    """Cache configuration."""

    redis_url: str


class CORSConfig(BaseModel):
    """CORS configuration."""

    allowed_origins: list[str] = ["*"]


class AppConfig(BaseModel):
    """Application configuration schema."""

    database: Optional[DatabaseConfig] = None
    swagger: Optional[SwaggerConfig] = None
    auth: Optional[AuthConfig] = None
    cache: Optional[CacheConfig] = None
    cors: Optional[CORSConfig] = None

