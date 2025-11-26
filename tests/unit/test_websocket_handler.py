"""Unit tests for WebSocket handler classes."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.rest_endpoint import RestEndpoint
from src.infrastructure.websocket.base import DefaultWebSocketHandler, WebSocketHandler


@pytest.fixture
def mockWebSocket() -> MagicMock:
    """Fixture for mock WebSocket object."""
    websocket = MagicMock()
    websocket.send_text = AsyncMock()
    websocket.send_json = AsyncMock()
    return websocket


@pytest.fixture
def mockModel() -> type[RestEndpoint]:
    """Fixture for mock RestEndpoint model."""
    from sqlalchemy import Column, Integer
    
    return type(
        "TestModel",
        (RestEndpoint,),
        {
            "__tablename__": "test_model",
            "id": Column(Integer, primary_key=True),
        },
    )


class TestWebSocketHandler:
    """Test suite for WebSocketHandler base class."""

    @pytest.mark.asyncio
    async def test_handler_instantiation(self) -> None:
        """Test that WebSocketHandler can be instantiated."""
        handler = WebSocketHandler()
        assert handler is not None
        assert isinstance(handler, WebSocketHandler)

    @pytest.mark.asyncio
    async def test_on_connect_default_implementation(
        self, mockWebSocket: MagicMock, mockModel: type[RestEndpoint]
    ) -> None:
        """Test on_connect() default implementation behavior."""
        handler = WebSocketHandler()

        with patch("src.infrastructure.websocket.base.logger") as mock_logger:
            await handler.on_connect(mockWebSocket, mockModel)

            # Verify logger was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "WebSocket connection established" in call_args
            assert "TestModel" in call_args

    @pytest.mark.asyncio
    async def test_on_message_default_implementation_echoes_message(
        self, mockWebSocket: MagicMock, mockModel: type[RestEndpoint]
    ) -> None:
        """Test on_message() default implementation echoes message back."""
        handler = WebSocketHandler()
        test_message = "Hello, WebSocket!"

        await handler.on_message(mockWebSocket, mockModel, test_message)

        # Verify send was called with echo response
        mockWebSocket.send_json.assert_called_once()
        call_args = mockWebSocket.send_json.call_args[0][0]
        assert call_args["message"] == "Received"
        assert call_args["data"] == test_message

    @pytest.mark.asyncio
    async def test_on_disconnect_default_implementation(
        self, mockWebSocket: MagicMock, mockModel: type[RestEndpoint]
    ) -> None:
        """Test on_disconnect() default implementation behavior."""
        handler = WebSocketHandler()

        with patch("src.infrastructure.websocket.base.logger") as mock_logger:
            await handler.on_disconnect(mockWebSocket, mockModel)

            # Verify logger was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "WebSocket connection closed" in call_args
            assert "TestModel" in call_args

    @pytest.mark.asyncio
    async def test_send_helper_with_string_message(self, mockWebSocket: MagicMock) -> None:
        """Test send() helper method with string message."""
        handler = WebSocketHandler()
        test_message = "Hello, client!"

        await handler.send(mockWebSocket, test_message)

        # Verify send_text was called
        mockWebSocket.send_text.assert_called_once_with(test_message)
        mockWebSocket.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_helper_with_dict_message(self, mockWebSocket: MagicMock) -> None:
        """Test send() helper method with dict message (JSON conversion)."""
        handler = WebSocketHandler()
        test_message = {"type": "notification", "message": "Hello"}

        await handler.send(mockWebSocket, test_message)

        # Verify send_json was called
        mockWebSocket.send_json.assert_called_once_with(test_message)
        mockWebSocket.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_helper_error_handling(self, mockWebSocket: MagicMock) -> None:
        """Test send() helper method error handling."""
        handler = WebSocketHandler()
        test_message = "Hello, client!"

        # Make send_text raise an exception
        mockWebSocket.send_text.side_effect = Exception("Connection closed")

        with patch("src.infrastructure.websocket.base.logger") as mock_logger:
            # Should not raise, should log error
            await handler.send(mockWebSocket, test_message)

            # Verify error was logged
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Error sending WebSocket message" in call_args


class TestDefaultWebSocketHandler:
    """Test suite for DefaultWebSocketHandler class."""

    @pytest.mark.asyncio
    async def test_default_handler_extends_base(
        self, mockWebSocket: MagicMock, mockModel: type[RestEndpoint]
    ) -> None:
        """Test that DefaultWebSocketHandler extends WebSocketHandler."""
        handler = DefaultWebSocketHandler()
        assert isinstance(handler, WebSocketHandler)

    @pytest.mark.asyncio
    async def test_default_handler_echoes_message(
        self, mockWebSocket: MagicMock, mockModel: type[RestEndpoint]
    ) -> None:
        """Test DefaultWebSocketHandler echoes messages (backward compatibility)."""
        handler = DefaultWebSocketHandler()
        test_message = "Test message"

        await handler.on_message(mockWebSocket, mockModel, test_message)

        # Verify echo behavior
        mockWebSocket.send_json.assert_called_once()
        call_args = mockWebSocket.send_json.call_args[0][0]
        assert call_args["message"] == "Received"
        assert call_args["data"] == test_message


class TestRestEndpointConfiguration:
    """Test suite for RestEndpoint.Configuration websocket_class validation."""

    def test_websocket_class_validation_with_valid_subclass(self) -> None:
        """Test validation passes with valid WebSocketHandler subclass."""

        class CustomHandler(WebSocketHandler):
            pass

        class TestModel(RestEndpoint):
            __tablename__ = "test_model"

            class Configuration:
                websocket_class = CustomHandler

        # Should not raise
        assert TestModel.Configuration.websocket_class == CustomHandler

    def test_websocket_class_validation_with_invalid_class(self) -> None:
        """Test validation raises error with invalid class."""
        from src.domain.errors import PylightError

        class NotAHandler:
            pass

        with pytest.raises(PylightError, match="must be a subclass of WebSocketHandler"):

            class TestModel(RestEndpoint):
                __tablename__ = "test_model"

                class Configuration:
                    websocket_class = NotAHandler

    def test_websocket_class_none_allowed(self) -> None:
        """Test that websocket_class can be None."""

        class TestModel(RestEndpoint):
            __tablename__ = "test_model"

            class Configuration:
                websocket_class = None

        # Should not raise
        config = TestModel.getConfiguration()
        assert config.websocket_class is None
