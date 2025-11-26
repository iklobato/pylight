"""YAML configuration loader."""

from pathlib import Path
from typing import Any, Dict

from src.domain.errors import ConfigurationError
from src.infrastructure.config.yaml_parser import YAMLParser


class YAMLLoader:
    """Loads configuration from YAML files."""

    @staticmethod
    def load(configPath: str | Path) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            configPath: Path to YAML configuration file

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        path = Path(configPath)
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {configPath}")

        try:
            with open(path, "r") as f:
                content = f.read()
                try:
                    config = YAMLParser.parse(content)
                    if config is None:
                        return {}
                    return config
                except ConfigurationError:
                    raise
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}") from e

