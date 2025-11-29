"""Test configuration class for integration examples."""

from typing import Any


class TestConfig:
    """Test configuration class."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/pylight"
    swagger_title: str = "Test API"
    swagger_version: str = "1.0.0"
    swagger_description: str = "Test API for configuration validation"

    cors_allowed_origins: list[str] = ["*"]
    cors_allowed_methods: list[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_allowed_headers: list[str] = ["*"]

