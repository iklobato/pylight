"""Plugin discovery mechanism."""

from typing import List, Type
from pathlib import Path

from src.domain.plugins.interface import Plugin
from src.infrastructure.plugins.loader import PluginLoader


class PluginDiscovery:
    """Discovers and loads plugins automatically."""

    @staticmethod
    def discoverFromDirectory(pluginDir: str) -> List[Type[Plugin]]:
        """Discover plugins from a directory.

        Args:
            pluginDir: Directory containing plugin files

        Returns:
            List of discovered plugin classes
        """
        plugins: List[Type[Plugin]] = []
        pluginPath = Path(pluginDir)

        if not pluginPath.exists():
            return plugins

        for pluginFile in pluginPath.glob("*.py"):
            if pluginFile.name.startswith("_"):
                continue
            try:
                pluginClass = PluginLoader.loadFromFile(str(pluginFile))
                plugins.append(pluginClass)
            except Exception:
                continue

        return plugins

