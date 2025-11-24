"""YAML configuration loader."""

from pathlib import Path
from typing import Any, Dict
import yaml

from src.domain.errors import ConfigurationError


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
                    config = yaml.safe_load(content)
                    if config is None:
                        return {}
                    return config
                except yaml.YAMLError as e:
                    lineNumber = getattr(e, "problem_mark", None)
                    if lineNumber:
                        lineNum = lineNumber.line + 1
                        context = ""
                        lines = content.split("\n")
                        if 0 <= lineNum - 1 < len(lines):
                            context = f" Context: {lines[lineNum - 1].strip()}"
                        raise ConfigurationError(
                            f"YAML syntax error at line {lineNum}: {str(e).split(chr(10))[0]}.{context}"
                        ) from e
                    raise ConfigurationError(f"Invalid YAML in configuration file: {e}") from e
        except ConfigurationError:
            raise
        except yaml.YAMLError as e:
            lineNumber = getattr(e, "problem_mark", None)
            if lineNumber:
                lineNum = lineNumber.line + 1
                raise ConfigurationError(
                    f"YAML syntax error at line {lineNum}: {str(e).split(chr(10))[0]}"
                ) from e
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}") from e

