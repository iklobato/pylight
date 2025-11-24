"""Plugin system interface."""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.presentation.app import LightApi


class Plugin:
    """Base class for plugins."""

    def initialize(self, app: "LightApi") -> None:
        """Initialize plugin with the application.

        Args:
            app: LightApi application instance
        """
        pass

    def register(self, app: "LightApi") -> None:
        """Register plugin components with the application.

        Args:
            app: LightApi application instance
        """
        pass

