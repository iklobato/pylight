# WebSocket Handler Classes

Documentation for WebSocket handler classes in Pylight.

## Implementation Notes

The WebSocket handler implementation follows clean code principles:
- Message loop is extracted to a separate function for better readability
- Error handling uses separate try-catch blocks for receive operations and handler method calls
- Early returns are used for connection setup failures
- No `else` statements are used in conditional logic

These implementation details are internal to the framework and do not affect how you use the WebSocket handlers.

## WebSocketHandler

Base class for WebSocket connection handling. Provides default implementations for all lifecycle methods that can be optionally overridden.

### Class Definition

```python
class WebSocketHandler:
    """Base class for WebSocket connection handling."""
```

### Methods

#### `on_connect`

Handle WebSocket connection establishment.

```python
async def on_connect(
    self, 
    websocket: WebSocket, 
    model: Type[RestEndpoint]
) -> None
```

**Parameters**:
- `websocket` (WebSocket): Starlette WebSocket connection object
- `model` (Type[RestEndpoint]): RestEndpoint model class for this connection

**Returns**:
- `None`

**Default Behavior**: Logs connection establishment.

**Example**:
```python
class CustomHandler(WebSocketHandler):
    async def on_connect(self, websocket, model):
        await self.send(websocket, {"status": "connected"})
```

#### `on_message`

Handle incoming WebSocket message.

```python
async def on_message(
    self, 
    websocket: WebSocket, 
    model: Type[RestEndpoint], 
    message: str
) -> None
```

**Parameters**:
- `websocket` (WebSocket): Starlette WebSocket connection object
- `model` (Type[RestEndpoint]): RestEndpoint model class for this connection
- `message` (str): Raw message string from client

**Returns**:
- `None`

**Default Behavior**: Echoes message back to client.

**Example**:
```python
class CustomHandler(WebSocketHandler):
    async def on_message(self, websocket, model, message):
        import json
        data = json.loads(message)
        await self.send(websocket, {"echo": data})
```

#### `on_disconnect`

Handle WebSocket connection closure.

```python
async def on_disconnect(
    self, 
    websocket: WebSocket, 
    model: Type[RestEndpoint]
) -> None
```

**Parameters**:
- `websocket` (WebSocket): Starlette WebSocket connection object
- `model` (Type[RestEndpoint]): RestEndpoint model class for this connection

**Returns**:
- `None`

**Default Behavior**: Logs disconnection.

**Example**:
```python
class CustomHandler(WebSocketHandler):
    async def on_disconnect(self, websocket, model):
        print(f"Client disconnected from {model.__name__}")
```

#### `send`

Helper method to send message to client.

```python
async def send(
    self, 
    websocket: WebSocket, 
    message: str | dict
) -> None
```

**Parameters**:
- `websocket` (WebSocket): Starlette WebSocket connection object
- `message` (str | dict): String or dict to send (dict auto-converted to JSON)

**Returns**:
- `None`

**Behavior**:
- If `message` is a dict, converts to JSON and sends via `websocket.send_json()`
- If `message` is a string, sends via `websocket.send_text()`
- Logs errors but does not raise exceptions

**Example**:
```python
class CustomHandler(WebSocketHandler):
    async def on_message(self, websocket, model, message):
        # Send string
        await self.send(websocket, "Hello, client!")
        
        # Send dict (auto-converted to JSON)
        await self.send(websocket, {"type": "notification", "message": "Update"})
```

## DefaultWebSocketHandler

Default WebSocket handler that matches current behavior for backward compatibility.

### Class Definition

```python
class DefaultWebSocketHandler(WebSocketHandler):
    """Default WebSocket handler that matches current behavior."""
```

### Behavior

- Extends `WebSocketHandler`
- Overrides `on_message()` to echo messages back to clients
- Used automatically when no custom `websocket_class` is specified in model Configuration

### Usage

The framework uses `DefaultWebSocketHandler` automatically when no custom handler is configured:

```python
class Product(RestEndpoint):
    __tablename__ = "products"
    # No websocket_class specified - uses DefaultWebSocketHandler
```

## Configuration

### RestEndpoint.Configuration.websocket_class

Configure a custom WebSocket handler class for a model.

**Type**: `Optional[Type[WebSocketHandler]]`

**Default**: `None` (uses `DefaultWebSocketHandler`)

**Example**:
```python
from pylight.infrastructure.websocket.base import WebSocketHandler

class CustomHandler(WebSocketHandler):
    async def on_message(self, websocket, model, message):
        await self.send(websocket, {"custom": "response"})

class Product(RestEndpoint):
    __tablename__ = "products"
    
    class Configuration:
        websocket_class = CustomHandler
```

**Validation**: The framework validates that `websocket_class` is a subclass of `WebSocketHandler` at model registration time. Invalid classes raise `PylightError`.

## Error Handling

All lifecycle methods are wrapped with error handling:

- **Exceptions in `on_connect()`**: Logged, connection closed gracefully, early return prevents further processing
- **Exceptions in `on_message()`**: Logged, connection closed gracefully, other connections continue. Receive errors and handler errors are handled separately for better error isolation
- **Exceptions in `on_disconnect()`**: Logged, cleanup continues
- **Exceptions in `send()`**: Logged, does not raise

Errors in one connection do not affect other connections. The framework uses separate error handling for receive operations and handler method calls to improve debugging and error isolation.

## Async Support

All methods are async and can perform async operations:

```python
class DatabaseHandler(WebSocketHandler):
    async def on_message(self, websocket, model, message):
        # Perform async database query
        result = await database.query(model).filter(...).first()
        await self.send(websocket, {"result": result})
```

Multiple connections execute async methods concurrently without blocking.

## See Also

- [WebSocket Documentation](../building-apis/websocket.md) for usage examples
- [Customization Guide](../customization/index.md) for advanced patterns
- [Configuration Options](configuration-options.md) for endpoint configuration

