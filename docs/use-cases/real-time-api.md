# Real-Time API

Complete example of creating a real-time API with WebSocket support.

## Overview

This use case demonstrates:
- WebSocket endpoint creation
- Real-time subscriptions
- Live updates on data changes

## Step 1: Define Model

```python
from src.presentation.app import LightApi
from src.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)
```

## Step 2: Create Application

```python
app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
app.run(host="localhost", port=8000)
```

WebSocket endpoint is automatically created at `/ws/products`.

## Step 3: Connect WebSocket

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8000/ws/products"
    async with websockets.connect(uri) as websocket:
        # Subscribe
        await websocket.send(json.dumps({
            "action": "subscribe",
            "resource": "products"
        }))
        
        # Listen for updates
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Event: {data['event']}, Data: {data['data']}")

asyncio.run(connect())
```

[View source: `docs/examples/websocket_hooks.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/websocket_hooks.py)

## Testing

### Create Product (triggers WebSocket update)

```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999}'
```

WebSocket clients receive update notification.

## Next Steps

- Learn about [WebSocket](../building-apis/websocket.md) for details
- Explore [GraphQL](../building-apis/graphql.md) for flexible queries

