# Quick Start

This guide will help you create your first Pylight API in minutes. By the end, you'll have a working API with REST endpoints, GraphQL, and WebSocket support.

## Step 1: Create a Model

Create a Python file (e.g., `app.py`) and define your first model:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)
```

[View source: `docs/examples/basic_usage.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/basic_usage.py)

## Step 2: Initialize the Application

Create a LightApi instance and register your model:

```python
app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
```

## Step 3: Run the Server

Start the development server:

```python
app.run(host="localhost", port=8000)
```

## Complete Example

Here's the complete `app.py` file:

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)

if __name__ == "__main__":
    app = LightApi(databaseUrl="sqlite:///app.db")
    app.register(Product)
    app.run(host="localhost", port=8000)
```

[View source: `docs/examples/basic_usage.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/basic_usage.py)

## Step 4: Test Your API

Once the server is running, you can access:

### REST Endpoints

- **List all products**: `GET http://localhost:8000/api/products`
- **Get a product**: `GET http://localhost:8000/api/products/{id}`
- **Create a product**: `POST http://localhost:8000/api/products`
- **Update a product**: `PUT http://localhost:8000/api/products/{id}`
- **Delete a product**: `DELETE http://localhost:8000/api/products/{id}`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### GraphQL

- **GraphiQL**: `http://localhost:8000/graphiql`
- **GraphQL Endpoint**: `http://localhost:8000/graphql`

### WebSocket

- **WebSocket Endpoint**: `ws://localhost:8000/ws/products`

## Example: Create a Product

Using curl:

```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999}'
```

Response:

```json
{
  "id": 1,
  "name": "Laptop",
  "price": 999
}
```

## Example: List Products

```bash
curl http://localhost:8000/api/products
```

Response:

```json
[
  {
    "id": 1,
    "name": "Laptop",
    "price": 999
  }
]
```

## Example: GraphQL Query

Visit `http://localhost:8000/graphiql` and try:

```graphql
query {
  products {
    id
    name
    price
  }
}
```

## What's Next?

Congratulations! You've created your first Pylight API. Now you can:

- Learn about [REST Endpoints](../building-apis/rest-endpoints.md) - Advanced REST features
- Explore [GraphQL](../building-apis/graphql.md) - GraphQL queries and mutations
- Add [Authentication](../building-apis/authentication.md) - Secure your API
- Configure [YAML Configuration](../building-apis/yaml-configuration.md) - Use YAML for configuration
- Check out [Use Cases](../use-cases/index.md) - Real-world examples

## Troubleshooting

### Database Not Found

If you see database errors, make sure the database file is created. SQLite will create the file automatically, but you may need to create tables first. Pylight will create tables automatically when you register models.

### Port Already in Use

If port 8000 is already in use, change it:

```python
app.run(host="localhost", port=8001)
```

### Import Errors

Make sure Pylight is installed:

```bash
pip install pylight
```

## Next Steps

- Read the [Architecture Overview](architecture.md) to understand how Pylight works
- Explore [Building APIs](../building-apis/index.md) for advanced features
- Check out [Use Cases](../use-cases/index.md) for real-world examples

