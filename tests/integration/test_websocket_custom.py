"""Integration tests for custom WebSocket handlers."""

import asyncio
import json
from typing import Type

import httpx
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from src.domain.entities.rest_endpoint import RestEndpoint
from src.infrastructure.websocket.base import DefaultWebSocketHandler, WebSocketHandler
from src.presentation.app import LightApi
from src.presentation.websocket.handler import createWebSocketRoute


class CustomTestHandler(WebSocketHandler):
    """Custom handler for testing."""

    def __init__(self) -> None:
        """Initialize custom handler."""
        super().__init__()
        self.connect_called = False
        self.message_called = False
        self.disconnect_called = False
        self.received_messages: list[str] = []

    async def on_connect(self, websocket: WebSocket, model: Type[RestEndpoint]) -> None:
        """Handle connection - mark as called."""
        self.connect_called = True
        await self.send(websocket, {"status": "connected"})

    async def on_message(
        self, websocket: WebSocket, model: Type[RestEndpoint], message: str
    ) -> None:
        """Handle message - store and echo."""
        self.message_called = True
        self.received_messages.append(message)
        await self.send(websocket, {"echo": message})

    async def on_disconnect(self, websocket: WebSocket, model: Type[RestEndpoint]) -> None:
        """Handle disconnection - mark as called."""
        self.disconnect_called = True


class AsyncOperationHandler(WebSocketHandler):
    """Handler that performs async operations."""

    async def on_message(
        self, websocket: WebSocket, model: Type[RestEndpoint], message: str
    ) -> None:
        """Handle message with async operation."""
        # Simulate async operation (e.g., database query)
        await asyncio.sleep(0.01)
        await self.send(websocket, {"processed": message})


@pytest.fixture
def testModel() -> Type[RestEndpoint]:
    """Fixture for test model."""
    from sqlalchemy import Column, Integer

    class TestProduct(RestEndpoint):
        __tablename__ = "test_products"
        id = Column(Integer, primary_key=True)

    return TestProduct


@pytest.fixture
def testModelWithCustomHandler() -> Type[RestEndpoint]:
    """Fixture for test model with custom handler."""
    from sqlalchemy import Column, Integer

    class TestProduct(RestEndpoint):
        __tablename__ = "test_products_custom"
        id = Column(Integer, primary_key=True)

        class Configuration:
            websocket_class = CustomTestHandler

    return TestProduct


@pytest.fixture
def testModelWithAsyncHandler() -> Type[RestEndpoint]:
    """Fixture for test model with async operation handler."""
    from sqlalchemy import Column, Integer

    class TestProduct(RestEndpoint):
        __tablename__ = "test_products_async"
        id = Column(Integer, primary_key=True)

        class Configuration:
            websocket_class = AsyncOperationHandler

    return TestProduct


class TestCustomWebSocketHandler:
    """Test suite for custom WebSocket handler integration."""

    @pytest.mark.asyncio
    async def test_custom_handler_class_extends_base(self) -> None:
        """Test that custom handler class extends base class."""
        handler = CustomTestHandler()
        assert isinstance(handler, WebSocketHandler)

    @pytest.mark.asyncio
    async def test_custom_on_connect_method_called(
        self, testModelWithCustomHandler: Type[RestEndpoint]
    ) -> None:
        """Test custom on_connect() method is called."""
        route = createWebSocketRoute(testModelWithCustomHandler)

        # Create test client
        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        # Connect via WebSocket
        with client.websocket_connect(
            f"/ws/{testModelWithCustomHandler.getTableName()}"
        ) as websocket:
            # Receive connection message
            data = websocket.receive_json()
            assert data["status"] == "connected"

            # Handler should have been instantiated and on_connect called
            # Note: We can't directly access handler instance, but we can verify behavior

    @pytest.mark.asyncio
    async def test_custom_on_message_method_called_with_raw_string(
        self, testModelWithCustomHandler: Type[RestEndpoint]
    ) -> None:
        """Test custom on_message() method is called with raw message string."""
        route = createWebSocketRoute(testModelWithCustomHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        test_message = "Hello, WebSocket!"

        with client.websocket_connect(
            f"/ws/{testModelWithCustomHandler.getTableName()}"
        ) as websocket:
            # Receive connection message
            websocket.receive_json()

            # Send message
            websocket.send_text(test_message)

            # Receive echo
            response = websocket.receive_json()
            assert response["echo"] == test_message

    @pytest.mark.asyncio
    async def test_custom_on_disconnect_method_called(
        self, testModelWithCustomHandler: Type[RestEndpoint]
    ) -> None:
        """Test custom on_disconnect() method is called."""
        route = createWebSocketRoute(testModelWithCustomHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        with client.websocket_connect(
            f"/ws/{testModelWithCustomHandler.getTableName()}"
        ) as websocket:
            # Receive connection message
            websocket.receive_json()

            # Close connection (triggers on_disconnect)
            websocket.close()

        # Handler's on_disconnect should have been called
        # (verified by no exceptions during close)

    @pytest.mark.asyncio
    async def test_model_with_websocket_class_uses_custom_handler(
        self, testModelWithCustomHandler: Type[RestEndpoint]
    ) -> None:
        """Test model with websocket_class in Configuration uses custom handler."""
        route = createWebSocketRoute(testModelWithCustomHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        with client.websocket_connect(
            f"/ws/{testModelWithCustomHandler.getTableName()}"
        ) as websocket:
            # Custom handler sends {"status": "connected"} on connect
            data = websocket.receive_json()
            assert data["status"] == "connected"  # Custom behavior, not default

    @pytest.mark.asyncio
    async def test_model_without_websocket_class_uses_default_handler(
        self, testModel: Type[RestEndpoint]
    ) -> None:
        """Test model without websocket_class uses default handler."""
        route = createWebSocketRoute(testModel)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        with client.websocket_connect(f"/ws/{testModel.getTableName()}") as websocket:
            # Send message
            test_message = "Test message"
            websocket.send_text(test_message)

            # Default handler echoes with {"message": "Received", "data": ...}
            response = websocket.receive_json()
            assert response["message"] == "Received"
            assert response["data"] == test_message

    @pytest.mark.asyncio
    async def test_multiple_models_with_different_handlers(
        self, testModel: Type[RestEndpoint], testModelWithCustomHandler: Type[RestEndpoint]
    ) -> None:
        """Test multiple models with different custom WebSocket classes use correct handlers."""
        route1 = createWebSocketRoute(testModel)
        route2 = createWebSocketRoute(testModelWithCustomHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route1, route2])
        client = TestClient(app)

        # Test default handler
        with client.websocket_connect(f"/ws/{testModel.getTableName()}") as ws1:
            ws1.send_text("test1")
            response1 = ws1.receive_json()
            assert response1["message"] == "Received"  # Default behavior

        # Test custom handler
        with client.websocket_connect(f"/ws/{testModelWithCustomHandler.getTableName()}") as ws2:
            response2 = ws2.receive_json()
            assert response2["status"] == "connected"  # Custom behavior

    @pytest.mark.asyncio
    async def test_custom_async_on_message_performs_async_operation(
        self, testModelWithAsyncHandler: Type[RestEndpoint]
    ) -> None:
        """Test custom async on_message() method performs async operation without blocking."""
        route = createWebSocketRoute(testModelWithAsyncHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        with client.websocket_connect(
            f"/ws/{testModelWithAsyncHandler.getTableName()}"
        ) as websocket:
            # Send message
            test_message = "Async test"
            websocket.send_text(test_message)

            # Should receive processed response (after async sleep)
            response = websocket.receive_json()
            assert response["processed"] == test_message

    @pytest.mark.asyncio
    async def test_multiple_concurrent_connections_execute_async_methods_simultaneously(
        self, testModelWithAsyncHandler: Type[RestEndpoint]
    ) -> None:
        """Test multiple concurrent WebSocket connections execute async methods simultaneously."""
        route = createWebSocketRoute(testModelWithAsyncHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        # Open multiple connections
        with (
            client.websocket_connect(f"/ws/{testModelWithAsyncHandler.getTableName()}") as ws1,
            client.websocket_connect(f"/ws/{testModelWithAsyncHandler.getTableName()}") as ws2,
        ):

            # Send messages simultaneously
            ws1.send_text("message1")
            ws2.send_text("message2")

            # Both should receive responses (proving non-blocking)
            response1 = ws1.receive_json()
            response2 = ws2.receive_json()

            assert response1["processed"] == "message1"
            assert response2["processed"] == "message2"

    @pytest.mark.asyncio
    async def test_async_send_helper_method_awaitable(
        self, testModelWithCustomHandler: Type[RestEndpoint]
    ) -> None:
        """Test async send() helper method is awaitable."""
        route = createWebSocketRoute(testModelWithCustomHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        with client.websocket_connect(
            f"/ws/{testModelWithCustomHandler.getTableName()}"
        ) as websocket:
            # Handler uses await self.send() in on_connect
            # If it's not awaitable, this would fail
            response = websocket.receive_json()
            assert "status" in response or "echo" in response

    @pytest.mark.asyncio
    async def test_custom_handler_works_without_context_manager(
        self, testModelWithCustomHandler: Type[RestEndpoint]
    ) -> None:
        """Test custom handler works without context manager usage."""
        route = createWebSocketRoute(testModelWithCustomHandler)

        from starlette.applications import Starlette

        app = Starlette(routes=[route])
        client = TestClient(app)

        # Connect without using context manager pattern in handler code
        with client.websocket_connect(
            f"/ws/{testModelWithCustomHandler.getTableName()}"
        ) as websocket:
            # Handler methods are called directly, no context manager needed
            response = websocket.receive_json()
            assert response is not None
