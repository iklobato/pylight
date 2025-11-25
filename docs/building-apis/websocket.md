# WebSocket

Pylight automatically generates WebSocket endpoints for real-time communication with your models.

## Overview

When you register a model, Pylight automatically creates:

- **WebSocket Endpoint**: Available at `/ws/{table_name}`
- **Real-time Updates**: Automatic notifications on create, update, delete
- **Subscription Model**: Subscribe to specific resources or events

## Basic Example

```python
from src.presentation.app import LightApi
from src.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)

app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
app.run(host="localhost", port=8000)
```

This automatically creates a WebSocket endpoint at `/ws/products`.

## WebSocket Connection

Connect to the WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/products');
```

Or using Python:

```python
import asyncio
import websockets

async def connect():
    uri = "ws://localhost:8000/ws/products"
    async with websockets.connect(uri) as websocket:
        # Send subscription message
        await websocket.send('{"action": "subscribe", "resource": "products"}')
        
        # Receive messages
        message = await websocket.recv()
        print(f"Received: {message}")

asyncio.run(connect())
```

## Subscription

Subscribe to receive updates:

```json
{
  "action": "subscribe",
  "resource": "products"
}
```

## Message Types

### Create Event

When a new item is created:

```json
{
  "event": "created",
  "resource": "products",
  "data": {
    "id": 1,
    "name": "Laptop",
    "price": 999
  }
}
```

### Update Event

When an item is updated:

```json
{
  "event": "updated",
  "resource": "products",
  "data": {
    "id": 1,
    "name": "Updated Laptop",
    "price": 1099
  }
}
```

### Delete Event

When an item is deleted:

```json
{
  "event": "deleted",
  "resource": "products",
  "data": {
    "id": 1
  }
}
```

## Client Example

Complete WebSocket client example:

```python
import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://localhost:8000/ws/products"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to products
        subscribe = {
            "action": "subscribe",
            "resource": "products"
        }
        await websocket.send(json.dumps(subscribe))
        
        # Listen for messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Event: {data['event']}, Data: {data['data']}")

asyncio.run(websocket_client())
```

[View source: `docs/examples/websocket_hooks.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/websocket_hooks.py)

## Multiple Connections

Multiple clients can connect simultaneously:

```python
async def multiple_clients():
    uri = "ws://localhost:8000/ws/products"
    
    # Connect multiple clients
    async with websockets.connect(uri) as ws1, \
              websockets.connect(uri) as ws2:
        
        # Both subscribe
        await ws1.send(json.dumps({"action": "subscribe", "resource": "products"}))
        await ws2.send(json.dumps({"action": "subscribe", "resource": "products"}))
        
        # Both receive updates
        msg1 = await ws1.recv()
        msg2 = await ws2.recv()
```

## Authentication

To require authentication for WebSocket connections, see [Authentication](authentication.md).

## Use Cases

WebSocket is ideal for:

- **Real-time Dashboards**: Live updates for monitoring
- **Collaborative Applications**: Multiple users editing simultaneously
- **Notifications**: Push updates to clients
- **Live Data Feeds**: Streaming data updates

## Advanced Examples

For more complex WebSocket examples, see:
- [WebSocket Hooks Example](https://github.com/iklobato/pylight/blob/main/docs/examples/websocket_hooks.py)
- [Use Cases](../use-cases/index.md) for real-world patterns

## Next Steps

- Learn about [REST Endpoints](rest-endpoints.md) for traditional APIs
- Explore [GraphQL](graphql.md) for flexible queries
- Add [Authentication](authentication.md) to secure WebSocket connections
- Check out [Use Cases](../use-cases/real-time-api.md) for real-time API examples

