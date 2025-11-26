# Pylight

A next-generation Python API framework that automatically generates REST endpoints, GraphQL schemas, WebSocket hooks, and CLI commands from data models.

## What is Pylight?

Pylight is a powerful Python framework that eliminates boilerplate code by automatically generating complete API endpoints from your SQLAlchemy models. Simply define your data models, and Pylight handles the rest - REST endpoints, GraphQL queries and mutations, WebSocket connections, and more.

## Key Benefits

- **Zero Boilerplate**: Define models, get full CRUD APIs automatically
- **Multiple Protocols**: REST, GraphQL, and WebSocket support out of the box
- **Production Ready**: Built on Starlette and Uvicorn for high-performance async operations
- **Flexible Configuration**: YAML or class-based configuration
- **Database Agnostic**: Works with PostgreSQL, MySQL, SQLite, and more
- **Extensible**: Plugin system for custom functionality

## Quick Start

Get started with Pylight in minutes:

```bash
# Install Pylight
pip install pylight

# Create a new project
pylight init my-api
cd my-api

# Run the server
python main.py
```

## Quick Example

Create a complete API with just a few lines of code:

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
- GraphQL endpoint at `/graphql`
- WebSocket endpoint at `/ws/products`
- API documentation at `/docs`

[View source: `docs/examples/basic_usage.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/basic_usage.py)

## Features

### Automatic Endpoint Generation
Define models using class-based inheritance with SQLAlchemy, and get REST, GraphQL, WebSocket, and CLI endpoints automatically.

### Async I/O
Built on Starlette and Uvicorn for high-performance async operations that scale.

### Authentication
Role-based JWT and OAuth2 authentication out of the box with easy customization.

### Caching
Redis integration for efficient caching of API responses.

### Built-in Features
Pagination, filtering, and sorting for list endpoints - no extra code needed.

### Auto Documentation
Swagger/OpenAPI and GraphiQL interfaces generated automatically.

### Flexible Configuration
YAML or class-based configuration at app and endpoint levels.

### Database Reflection
Automatically generate models from existing databases.

### Extensible
Plugin system and inheritance-based customization for advanced use cases.

## Get Started

Ready to build your API? Start with our [Getting Started Guide](getting-started/index.md).

## Documentation Sections

- **[Getting Started](getting-started/index.md)** - Installation, quick start, and architecture overview
- **[Building APIs](building-apis/index.md)** - Complete guide to all framework features
- **[Customization](customization/index.md)** - Advanced configuration and customization
- **[API Reference](api-reference/index.md)** - Complete API documentation
- **[Use Cases](use-cases/index.md)** - Real-world examples and patterns
- **[Troubleshooting](troubleshooting/index.md)** - Common issues and solutions

## Requirements

- Python 3.11+
- SQLAlchemy-compatible database (PostgreSQL, MySQL, SQLite)

## License

MIT

