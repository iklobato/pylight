"""Class-based configuration loader."""

from typing import Any, Dict, Type
from pydantic import BaseModel


class ClassLoader:
    """Loads configuration from Python classes."""

    @staticmethod
    def load(configClass: Type[BaseModel] | Type[Any]) -> Dict[str, Any]:
        """Load configuration from a class.

        Args:
            configClass: Configuration class (Pydantic model or dataclass)

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If class cannot be converted to dict
        """
        try:
            if isinstance(configClass, type) and issubclass(configClass, BaseModel):
                instance = configClass()
                return instance.model_dump()
            elif hasattr(configClass, "__dict__"):
                return dict(configClass.__dict__)
            else:
                return {}
        except Exception as e:
            raise ConfigurationError(f"Error loading class configuration: {e}") from e

