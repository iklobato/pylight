"""WebSocket hook generator."""

from typing import Any, Type

from src.domain.entities.rest_endpoint import RestEndpoint


class WebSocketHookGenerator:
    """Generates WebSocket hooks from RestEndpoint models."""

    @staticmethod
    def generateHooks(model: Type[RestEndpoint]) -> dict[str, Any]:
        """Generate WebSocket hooks for a model.

        Args:
            model: Model class

        Returns:
            Dictionary of WebSocket hook configurations
        """
        return {
            "model": model.__name__,
            "hooks": ["create", "update", "delete"],
        }

