"""Base RestEndpoint class for all models."""

from typing import Any, Optional, Type
from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

from src.domain.errors import PylightError


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class RestEndpoint(Base):
    """Base class for all REST endpoints/models.

    Models should inherit from this class and define SQLAlchemy columns.
    The class name (lowercase) is used as the table name.
    """

    __abstract__ = True

    class Configuration:
        """Endpoint-level configuration.

        Subclasses can override this nested class to configure:
        - authentication_class: Custom authentication class
        - required_roles: Dictionary mapping HTTP method to list of required roles
        - caching_class: Custom caching class
        - caching_method_names: List of HTTP methods to cache
        - pagination_class: Custom pagination class
        """

        authentication_class: Optional[Type[Any]] = None
        required_roles: dict[str, list[str]] = {}
        caching_class: Optional[Type[Any]] = None
        caching_method_names: list[str] = []
        pagination_class: Optional[Type[Any]] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate subclass configuration."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "Configuration"):
            cls.Configuration = type("Configuration", (), {})
        if not isinstance(cls.Configuration, type):
            raise PylightError(
                f"{cls.__name__}.Configuration must be a class, not an instance"
            )

    @classmethod
    def getConfiguration(cls) -> Any:
        """Get endpoint-level configuration instance.

        Returns:
            Configuration instance
        """
        if hasattr(cls, "Configuration") and isinstance(cls.Configuration, type):
            return cls.Configuration()
        return type("Configuration", (), {})()

    @classmethod
    def getTableName(cls) -> str:
        """Get the table name for this model.
        
        Returns __tablename__ if defined, otherwise lowercase class name.
        """
        if hasattr(cls, "__tablename__") and cls.__tablename__:
            return cls.__tablename__
        return cls.__name__.lower()

