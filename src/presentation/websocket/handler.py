"""WebSocket handler."""

import logging
from typing import Any, Dict, Set, Type

from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from src.domain.entities.rest_endpoint import RestEndpoint
from src.infrastructure.websocket.base import DefaultWebSocketHandler, WebSocketHandler

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        self.connections: Dict[str, Set[WebSocket]] = {}

    def addConnection(self, modelName: str, websocket: WebSocket) -> None:
        """Add a WebSocket connection.

        Args:
            modelName: Model name for the connection
            websocket: WebSocket connection
        """
        if modelName not in self.connections:
            self.connections[modelName] = set()
        self.connections[modelName].add(websocket)

    def removeConnection(self, modelName: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            modelName: Model name for the connection
            websocket: WebSocket connection
        """
        if modelName in self.connections:
            self.connections[modelName].discard(websocket)
            if not self.connections[modelName]:
                del self.connections[modelName]

    async def broadcast(self, modelName: str, eventType: str, data: Dict[str, Any]) -> None:
        """Broadcast a message to all connections for a model.

        Args:
            modelName: Model name
            eventType: Event type (create, update, delete)
            data: Event data
        """
        if modelName not in self.connections:
            return

        message = {
            "type": eventType,
            "model": modelName,
            "data": data,
        }

        disconnected = set()
        for websocket in self.connections[modelName]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        for websocket in disconnected:
            self.removeConnection(modelName, websocket)


_websocketManager = WebSocketManager()


def getWebSocketManager() -> WebSocketManager:
    """Get the global WebSocket manager instance.

    Returns:
        WebSocketManager instance
    """
    return _websocketManager


async def _handleMessageLoop(
    websocket: WebSocket,
    handler: WebSocketHandler,
    model: Type[RestEndpoint],
    tableName: str,
) -> None:
    """Handle WebSocket message loop.

    Args:
        websocket: Starlette WebSocket connection
        handler: WebSocket handler instance
        model: RestEndpoint model class
        tableName: Table name for logging
    """
    while True:
        # Separate try-catch for receive operation
        try:
            data = await websocket.receive_text()
        except Exception:
            # Connection closed or error receiving
            break

        # Separate try-catch for handler method call
        try:
            await handler.on_message(websocket, model, data)
        except Exception as e:
            logger.error(
                f"Error in on_message for {tableName}: {e}",
                exc_info=True,
            )
            await websocket.close(code=1011, reason="Internal error")
            break


def createWebSocketRoute(model: Type[RestEndpoint]) -> WebSocketRoute:
    """Create WebSocket route for a model.

    Args:
        model: Model class

    Returns:
        Starlette WebSocketRoute
    """
    tableName = model.getTableName()
    manager = getWebSocketManager()

    # Get websocket_class from Configuration, use DefaultWebSocketHandler if None
    config = model.getConfiguration()
    handler_class: Type[WebSocketHandler] = DefaultWebSocketHandler
    if hasattr(config, "websocket_class") and config.websocket_class is not None:
        handler_class = config.websocket_class

    async def websocketHandler(websocket: WebSocket) -> None:
        """Handle WebSocket connections."""
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for {tableName}")
        manager.addConnection(tableName, websocket)

        # Instantiate handler class (per connection)
        handler = handler_class()
        logger.debug(f"Instantiated {handler_class.__name__} for {tableName}")

        # Call on_connect with error handling - use early return on error
        try:
            await handler.on_connect(websocket, model)
        except Exception as e:
            logger.error(
                f"Error in on_connect for {tableName}: {e}",
                exc_info=True,
            )
            await websocket.close(code=1011, reason="Internal error")
            manager.removeConnection(tableName, websocket)
            logger.info(f"WebSocket connection closed for {tableName}")
            return

        # Message loop (extracted to separate function)
        try:
            await _handleMessageLoop(websocket, handler, model, tableName)
        except Exception as e:
            logger.error(
                f"WebSocket connection error for {tableName}: {e}",
                exc_info=True,
            )
        finally:
            # Call on_disconnect with error handling
            try:
                await handler.on_disconnect(websocket, model)
            except Exception as e:
                logger.error(
                    f"Error in on_disconnect for {tableName}: {e}",
                    exc_info=True,
                )
            manager.removeConnection(tableName, websocket)
            logger.info(f"WebSocket connection closed for {tableName}")

    return WebSocketRoute(f"/ws/{tableName}", websocketHandler)
