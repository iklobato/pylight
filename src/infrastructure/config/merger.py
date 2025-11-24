"""Configuration merger for combining multiple config sources."""

from typing import Any, Dict


class ConfigMerger:
    """Merges configuration from multiple sources."""

    @staticmethod
    def merge(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries.

        Args:
            *configs: Configuration dictionaries to merge

        Returns:
            Merged configuration dictionary
        """
        merged: Dict[str, Any] = {}
        for config in configs:
            if config:
                merged = ConfigMerger._deepMerge(merged, config)
        return merged

    @staticmethod
    def _deepMerge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            update: Dictionary to merge into base

        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigMerger._deepMerge(result[key], value)
            else:
                result[key] = value
        return result

