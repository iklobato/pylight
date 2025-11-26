"""Base WebSocket handler class."""

import json
import logging
from typing import Type

from starlette.websockets import WebSocket

from src.domain.entities.rest_endpoint import RestEndpoint

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Base class for WebSocket connection handling.

    Provides default implementations for all lifecycle methods that can be
    optionally overridden. All methods are async and can perform async operations.
    """

    async def on_connect(self, websocket: WebSocket, model: Type[RestEndpoint]) -> None:
        """Handle WebSocket connection establishment.

        Args:
            websocket: Starlette WebSocket connection object
            model: RestEndpoint model class for this connection
        """
        logger.info(f"WebSocket connection established for model: {model.__name__}")

    async def on_message(
        self, websocket: WebSocket, model: Type[RestEndpoint], message: str
    ) -> None:
        """Handle incoming WebSocket message.

        Args:
            websocket: Starlette WebSocket connection object
            model: RestEndpoint model class for this connection
            message: Raw message string from client
        """
        # Default implementation: echo message back
        await self.send(websocket, {"message": "Received", "data": message})

    async def on_disconnect(self, websocket: WebSocket, model: Type[RestEndpoint]) -> None:
        """Handle WebSocket connection closure.

        Args:
            websocket: Starlette WebSocket connection object
            model: RestEndpoint model class for this connection
        """
        logger.info(f"WebSocket connection closed for model: {model.__name__}")

    async def send(self, websocket: WebSocket, message: str | dict) -> None:
        """Helper method to send message to client.

        Args:
            websocket: Starlette WebSocket connection object
            message: String or dict to send (dict auto-converted to JSON)
        """
        try:
            if isinstance(message, dict):
                await websocket.send_json(message)
            else:
                await websocket.send_text(str(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}", exc_info=True)


class DefaultWebSocketHandler(WebSocketHandler):
    """Default WebSocket handler that matches current behavior.

    Echoes messages back to clients, matching the existing WebSocket
    implementation behavior for backward compatibility.
    """

    async def on_message(
        self, websocket: WebSocket, model: Type[RestEndpoint], message: str
    ) -> None:
        """Handle incoming WebSocket message - echo behavior.

        Args:
            websocket: Starlette WebSocket connection object
            model: RestEndpoint model class for this connection
            message: Raw message string from client
        """
        await self.send(websocket, {"message": "Received", "data": message})
