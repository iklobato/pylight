"""Plugin loader."""

from typing import Type
from pathlib import Path
import importlib.util

from src.domain.plugins.interface import Plugin
from src.domain.errors import ConfigurationError


class PluginLoader:
    """Loads plugins from files or packages."""

    @staticmethod
    def loadFromFile(pluginPath: str) -> Type[Plugin]:
        """Load a plugin from a Python file.

        Args:
            pluginPath: Path to plugin file

        Returns:
            Plugin class

        Raises:
            ConfigurationError: If plugin cannot be loaded
        """
        path = Path(pluginPath)
        if not path.exists():
            raise ConfigurationError(f"Plugin file not found: {pluginPath}")

        try:
            spec = importlib.util.spec_from_file_location("plugin", path)
            if spec is None or spec.loader is None:
                raise ConfigurationError(f"Could not load plugin from {pluginPath}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attrName in dir(module):
                attr = getattr(module, attrName)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    return attr

            raise ConfigurationError(f"No Plugin class found in {pluginPath}")
        except Exception as e:
            raise ConfigurationError(f"Error loading plugin: {e}") from e

    @staticmethod
    def loadFromPackage(packageName: str) -> Type[Plugin]:
        """Load a plugin from an installed package.

        Args:
            packageName: Package name

        Returns:
            Plugin class

        Raises:
            ConfigurationError: If plugin cannot be loaded
        """
        try:
            module = importlib.import_module(packageName)
            for attrName in dir(module):
                attr = getattr(module, attrName)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    return attr

            raise ConfigurationError(f"No Plugin class found in package {packageName}")
        except ImportError as e:
            raise ConfigurationError(f"Could not import plugin package {packageName}: {e}") from e

