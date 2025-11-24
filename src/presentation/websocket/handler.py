"""WebSocket handler."""

from typing import Any, Dict, List, Set, Type
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket
import asyncio

from src.domain.entities.rest_endpoint import RestEndpoint


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


def createWebSocketRoute(model: Type[RestEndpoint]) -> WebSocketRoute:
    """Create WebSocket route for a model.

    Args:
        model: Model class

    Returns:
        Starlette WebSocketRoute
    """
    tableName = model.getTableName()
    manager = getWebSocketManager()

    async def websocketHandler(websocket: WebSocket) -> None:
        """Handle WebSocket connections."""
        await websocket.accept()
        manager.addConnection(tableName, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_json({"message": "Received", "data": data})
        except Exception:
            pass
        finally:
            manager.removeConnection(tableName, websocket)

    return WebSocketRoute(f"/ws/{tableName}", websocketHandler)

