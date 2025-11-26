# Pylight

A next-generation Python API framework that automatically generates REST endpoints, GraphQL schemas, WebSocket hooks, and CLI commands from data models.

## Features

- **Automatic Endpoint Generation**: Define models using class-based inheritance with SQLAlchemy, and get REST, GraphQL, WebSocket, and CLI endpoints automatically
- **Async I/O**: Built on Starlette and Uvicorn for high-performance async operations
- **Authentication**: Role-based JWT and OAuth2 authentication out of the box
- **Caching**: Redis integration for efficient caching
- **Built-in Features**: Pagination, filtering, and sorting for list endpoints
- **Auto Documentation**: Swagger/OpenAPI and GraphiQL interfaces generated automatically
- **Flexible Configuration**: YAML or class-based configuration at app and endpoint levels
- **Database Reflection**: Automatically generate models from existing databases
- **Extensible**: Plugin system and inheritance-based customization

## Quick Start

```bash
# Install
pip install pylight

# Create a new project
pylight init my-api
cd my-api

# Run the server
python main.py
```

## Quick Example

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
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

## Architecture

Pylight follows a clean layered architecture:

- **Domain**: Business logic and base entities
- **Application**: Endpoint generation and orchestration
- **Infrastructure**: Database, cache, auth, configuration
- **Presentation**: REST, GraphQL, WebSocket handlers using Starlette

## Examples

### REST Endpoints

Pylight automatically generates REST endpoints (GET, POST, PUT, DELETE) for your models:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
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

This automatically creates:
- `GET /api/products` - List all products
- `GET /api/products/{id}` - Get a specific product
- `POST /api/products` - Create a new product
- `PUT /api/products/{id}` - Update a product
- `DELETE /api/products/{id}` - Delete a product

For more complex examples, see [docs/examples/rest_endpoints.py](docs/examples/rest_endpoints.py).

### GraphQL

GraphQL queries and mutations are automatically generated:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
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

Access GraphiQL at `http://localhost:8000/graphiql` and use queries like:

```graphql
query {
  products(page: 1, limit: 10) {
    items {
      id
      name
      price
    }
    total
  }
}

mutation {
  createProduct(data: {name: "New Product", price: 99}) {
    id
    name
    price
  }
}
```

For more examples, see [docs/examples/graphql_queries.py](docs/examples/graphql_queries.py).

### WebSocket

Real-time updates via WebSocket connections. Customize WebSocket behavior by extending the base handler class:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from pylight.infrastructure.websocket.base import WebSocketHandler
from starlette.websockets import WebSocket
from sqlalchemy import Column, Integer, String
from typing import Type
import json

class CustomProductHandler(WebSocketHandler):
    """Custom WebSocket handler for Product model."""
    
    async def on_connect(self, websocket: WebSocket, model: Type[RestEndpoint]) -> None:
        """Send welcome message on connection."""
        await self.send(websocket, {"status": "connected", "message": "Welcome!"})
    
    async def on_message(self, websocket: WebSocket, model: Type[RestEndpoint], message: str) -> None:
        """Handle incoming messages."""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                await self.send(websocket, {"status": "subscribed"})
                return
            
            if action == "ping":
                await self.send(websocket, {"action": "pong"})
                return
        except json.JSONDecodeError:
            await self.send(websocket, {"error": "Invalid JSON"})

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)
    
    class Configuration:
        websocket_class = CustomProductHandler  # Optional: customize WebSocket behavior

app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
app.run(host="localhost", port=8000)
```

WebSocket endpoints are automatically created at `/ws/{table_name}`. If no custom handler is specified, the default handler echoes messages back to clients.

For more examples, see [docs/examples/custom_websocket_handler.py](docs/examples/custom_websocket_handler.py).

### Authentication

Enable JWT authentication for your endpoints:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from pylight.infrastructure.auth.jwt import DefaultJWTAuthentication
from sqlalchemy import Column, Integer, String
import jwt
import os

class User(RestEndpoint):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(100))
    role = Column(String(20), default="user")
    
    class Configuration:
        authentication_class = DefaultJWTAuthentication
        required_roles = ["admin"]  # Optional: restrict to specific roles

app = LightApi(databaseUrl="sqlite:///app.db")
app.register(User)
app.run(host="localhost", port=8000)

# Generate JWT token
secret_key = os.getenv("JWT_SECRET", "your-secret-key")
token = jwt.encode(
    {"username": "admin", "role": "admin", "sub": "1"},
    secret_key,
    algorithm="HS256"
)

# Use token in requests
# headers = {"Authorization": f"Bearer {token}"}
```

For OAuth2 authentication, see the authentication examples in the framework documentation.

### Caching

Enable Redis caching for improved performance:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from pylight.infrastructure.cache.redis import DefaultRedisCache
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)
    
    class Configuration:
        caching_class = DefaultRedisCache
        caching_method_names = ["GET"]  # Cache GET requests

app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)

# Note: Redis must be running for caching to work
# Install: pip install redis
# Start Redis: redis-server

app.run(host="localhost", port=8000)
```

Caching requires Redis to be installed and running. GET requests are cached automatically.

### Pagination, Filtering, and Sorting

Built-in support for pagination, filtering, and sorting:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
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

Use query parameters:
- `GET /api/products?page=1&limit=10` - Pagination
- `GET /api/products?price__gt=100` - Filter (price > 100)
- `GET /api/products?sort=-price` - Sort by price descending
- `GET /api/products?name__like=book&sort=price` - Combine filters and sorting

### Configuration

Configure your app using YAML or class-based configuration:

**YAML Configuration:**

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)

# config.yaml:
# database:
#   url: sqlite:///app.db
# swagger:
#   title: My API
#   version: 1.0.0

app = LightApi(configPath="config.yaml")
app.register(Product)
app.run(host="localhost", port=8000)
```

**Class-based Configuration:**

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)

class AppConfig:
    database = {"url": "sqlite:///app.db"}
    swagger = {"title": "My API", "version": "1.0.0"}

app = LightApi(configClass=AppConfig)
app.register(Product)
app.run(host="localhost", port=8000)
```

### Database Reflection

Generate models automatically from existing databases:

```bash
# Reflect models from database
pylight reflect --database-url postgresql://user:pass@localhost/mydb --output-dir models/

# This generates model files based on your database schema
```

The generated models can be used directly with Pylight:

```python
from models.product import Product  # Generated model
from pylight.presentation.app import LightApi

app = LightApi(databaseUrl="postgresql://user:pass@localhost/mydb")
app.register(Product)
app.run(host="localhost", port=8000)
```

### Plugin System

Extend Pylight with custom plugins:

```python
from pylight.presentation.app import LightApi
from pylight.domain.plugins.interface import Plugin
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)

class CustomPlugin(Plugin):
    def initialize(self, app):
        print("Plugin initialized")
    
    def register(self, app):
        # Add custom routes, middleware, etc.
        pass

app = LightApi(databaseUrl="sqlite:///app.db")
app.pluginRegistry.register(CustomPlugin)
app.register(Product)
app.run(host="localhost", port=8000)
```

## Requirements

- Python 3.11+
- SQLAlchemy-compatible database (PostgreSQL, MySQL, SQLite)

## License

MIT

