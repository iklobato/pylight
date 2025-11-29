# WebSocket Real-time Features Test Procedures

This document provides step-by-step procedures for testing WebSocket connections with external databases.

## Prerequisites

- Pylight API running and accessible
- External database with test data
- WebSocket client tool (e.g., `websocat`, browser console, or Python `websocket-client`)

## Step 1: Establish WebSocket Connection

### Using Python websocket-client

```python
import websocket
import json

# Connect to WebSocket endpoint
ws = websocket.create_connection("ws://localhost:8000/ws/products")

# Verify connection is established
print("WebSocket connected:", ws.connected)
```

### Using websocat (command line)

```bash
websocat ws://localhost:8000/ws/products
```

### Using Browser Console

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/products');
ws.onopen = () => console.log('WebSocket connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
ws.onclose = () => console.log('WebSocket closed');
```

## Step 2: Test Real-time Updates

1. **Establish WebSocket connection** (see Step 1)

2. **Create a new record via REST API**:
```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": "99.99", "sku": "NEW-001"}'
```

3. **Verify WebSocket receives notification**:
   - Connection should receive a message about the new record
   - Message should contain record data or notification

4. **Update a record via REST API**:
```bash
curl -X PUT http://localhost:8000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Product"}'
```

5. **Verify WebSocket receives update notification**

6. **Delete a record via REST API**:
```bash
curl -X DELETE http://localhost:8000/api/products/1
```

7. **Verify WebSocket receives deletion notification**

## Step 3: Test Multiple Connections

1. **Open multiple WebSocket connections** to the same table:
```python
import websocket
import threading

def connect_ws(name):
    ws = websocket.create_connection("ws://localhost:8000/ws/products")
    print(f"{name} connected")
    return ws

# Create multiple connections
ws1 = connect_ws("Connection 1")
ws2 = connect_ws("Connection 2")
ws3 = connect_ws("Connection 3")
```

2. **Make a database change** (create/update/delete)

3. **Verify all connections receive the notification**

4. **Close connections**:
```python
ws1.close()
ws2.close()
ws3.close()
```

## Step 4: Test Connection Interruption Handling

1. **Establish WebSocket connection**

2. **Simulate network interruption**:
   - Disconnect network temporarily
   - Or close connection abruptly

3. **Verify reconnection behavior**:
   - Connection should attempt to reconnect
   - Or gracefully handle disconnection

4. **Resume connection and verify it works**

## Step 5: Test Different Tables

Test WebSocket connections for different tables:

- `/ws/products`
- `/ws/users`
- `/ws/orders`

Each should receive updates specific to that table.

## Troubleshooting

### Connection Refused

- Verify Pylight is running
- Check WebSocket endpoint is enabled in configuration
- Verify firewall/network allows WebSocket connections

### No Updates Received

- Verify database changes are actually happening
- Check WebSocket is subscribed to correct table
- Verify WebSocket feature is enabled in Pylight config

### Connection Drops Frequently

- Check network stability
- Verify Pylight is not restarting
- Check for timeout configurations

