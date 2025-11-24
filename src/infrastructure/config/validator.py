"""Configuration validator."""

from typing import Any, Dict

from src.domain.errors import ConfigurationError
from src.infrastructure.config.schema import AppConfig


class ConfigValidator:
    """Validates configuration against schema."""

    @staticmethod
    def validate(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Validated configuration dictionary

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            appConfig = AppConfig(**config)
            return appConfig.model_dump(exclude_none=True)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

