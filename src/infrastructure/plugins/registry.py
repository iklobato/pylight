"""Plugin registry."""

from typing import List, Type, TYPE_CHECKING
from src.domain.plugins.interface import Plugin

if TYPE_CHECKING:
    from src.presentation.app import LightApi


class PluginRegistry:
    """Registry for managing plugins."""

    def __init__(self) -> None:
        """Initialize plugin registry."""
        self.plugins: List[Type[Plugin]] = []
        self.initializedPlugins: List[Plugin] = []

    def register(self, pluginClass: Type[Plugin]) -> None:
        """Register a plugin class.

        Args:
            pluginClass: Plugin class to register
        """
        if not issubclass(pluginClass, Plugin):
            raise ValueError(f"{pluginClass.__name__} must inherit from Plugin")
        self.plugins.append(pluginClass)

    def initialize(self, app: "LightApi") -> None:
        """Initialize all registered plugins.

        Args:
            app: LightApi application instance
        """
        for pluginClass in self.plugins:
            pluginInstance = pluginClass()
            pluginInstance.initialize(app)
            pluginInstance.register(app)
            self.initializedPlugins.append(pluginInstance)

    def getPlugins(self) -> List[Plugin]:
        """Get all initialized plugins.

        Returns:
            List of plugin instances
        """
        return self.initializedPlugins

