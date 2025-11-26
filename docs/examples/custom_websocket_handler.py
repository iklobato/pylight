"""Example: Custom WebSocket Handler

This example demonstrates how to create and use custom WebSocket handlers
using the class-based method override pattern.
"""

import json
import os
import sys

# Add parent directory to path to import framework
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Type

from sqlalchemy import Column, Integer, String
from starlette.websockets import WebSocket

from pylight.domain.entities.rest_endpoint import RestEndpoint
from pylight.infrastructure.websocket.base import WebSocketHandler
from pylight.presentation.app import LightApi


# Example 1: Basic Custom Handler
class BasicCustomHandler(WebSocketHandler):
    """Basic custom handler that sends welcome message on connect."""

    async def on_connect(self, websocket: WebSocket, model: Type[RestEndpoint]) -> None:
        """Send welcome message when client connects."""
        await self.send(
            websocket, {"type": "connected", "message": f"Welcome to {model.__name__} WebSocket!"}
        )


# Example 2: Handler with Message Parsing
class MessageParsingHandler(WebSocketHandler):
    """Handler that parses JSON messages and responds accordingly."""

    async def on_message(
        self, websocket: WebSocket, model: Type[RestEndpoint], message: str
    ) -> None:
        """Parse JSON message and respond based on action."""
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe":
                await self.send(
                    websocket, {"status": "subscribed", "resource": data.get("resource", "unknown")}
                )
                return

            if action == "ping":
                await self.send(websocket, {"action": "pong"})
                return

            if action == "echo":
                await self.send(websocket, {"echo": data.get("text", "")})
                return

            # Unknown action
            await self.send(websocket, {"error": "Unknown action", "received": data})
        except json.JSONDecodeError:
            await self.send(websocket, {"error": "Invalid JSON"})


# Example 3: Handler with Async Operations
class AsyncOperationHandler(WebSocketHandler):
    """Handler that performs async operations (e.g., database queries)."""

    async def on_message(
        self, websocket: WebSocket, model: Type[RestEndpoint], message: str
    ) -> None:
        """Process message with async operations."""
        try:
            data = json.loads(message)
            product_id = data.get("product_id")

            # Simulate async database query
            # In real usage, you would do:
            # result = await session.query(model).filter(model.id == product_id).first()

            # For this example, just echo with processing indicator
            await self.send(
                websocket,
                {"status": "processed", "product_id": product_id, "message": "Query completed"},
            )
        except Exception as e:
            await self.send(websocket, {"error": str(e)})


# Example 4: Handler with Authentication
class AuthenticatedHandler(WebSocketHandler):
    """Handler that validates authentication on connect."""

    async def on_connect(self, websocket: WebSocket, model: Type[RestEndpoint]) -> None:
        """Validate authentication token from query params."""
        token = websocket.query_params.get("token")

        if not token or not self.validate_token(token):
            await websocket.close(code=1008, reason="Unauthorized")
            return

        await self.send(websocket, {"status": "authenticated"})

    def validate_token(self, token: str) -> bool:
        """Validate authentication token (example implementation)."""
        # In real usage, validate JWT or session token
        return token == "valid_token_example"


# Example Models with Custom Handlers
class Product(RestEndpoint):
    """Product model with basic custom handler."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)

    class Configuration:
        websocket_class = BasicCustomHandler


class Order(RestEndpoint):
    """Order model with message parsing handler."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    total = Column(Integer)

    class Configuration:
        websocket_class = MessageParsingHandler


class Inventory(RestEndpoint):
    """Inventory model with async operations handler."""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    quantity = Column(Integer)

    class Configuration:
        websocket_class = AsyncOperationHandler


# Example Usage
def main():
    """Example application using custom WebSocket handlers."""
    app = LightApi(databaseUrl="sqlite:///example.db")

    # Register models with custom handlers
    app.register(Product)  # Uses BasicCustomHandler
    app.register(Order)  # Uses MessageParsingHandler
    app.register(Inventory)  # Uses AsyncOperationHandler

    print("Starting server with custom WebSocket handlers...")
    print("- Product WebSocket: /ws/products (BasicCustomHandler)")
    print("- Order WebSocket: /ws/orders (MessageParsingHandler)")
    print("- Inventory WebSocket: /ws/inventory (AsyncOperationHandler)")

    app.run(host="localhost", port=8000)


if __name__ == "__main__":
    main()
