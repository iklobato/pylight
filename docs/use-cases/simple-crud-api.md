# Simple CRUD API

Complete example of creating a simple CRUD API with Pylight.

## Overview

This use case demonstrates:
- Creating a model
- Registering with LightApi
- All CRUD operations (Create, Read, Update, Delete)
- Automatic endpoint generation

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
    description = Column(String(500))
```

[View source: `docs/examples/basic_usage.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/basic_usage.py)

## Step 2: Create Application

```python
app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
```

## Step 3: Run Server

```python
app.run(host="localhost", port=8000)
```

## Complete Example

```python
from src.presentation.app import LightApi
from src.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)
    description = Column(String(500))

if __name__ == "__main__":
    app = LightApi(databaseUrl="sqlite:///app.db")
    app.register(Product)
    app.run(host="localhost", port=8000)
```

## Available Endpoints

- `GET /api/products` - List all products
- `GET /api/products/{id}` - Get a product
- `POST /api/products` - Create a product
- `PUT /api/products/{id}` - Update a product
- `DELETE /api/products/{id}` - Delete a product

## Testing

### Create Product

```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop", "price": 999, "description": "High-performance laptop"}'
```

### List Products

```bash
curl http://localhost:8000/api/products
```

### Get Product

```bash
curl http://localhost:8000/api/products/1
```

### Update Product

```bash
curl -X PUT http://localhost:8000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Laptop", "price": 1099}'
```

### Delete Product

```bash
curl -X DELETE http://localhost:8000/api/products/1
```

## Next Steps

- Add [Authentication](../building-apis/authentication.md) to secure the API
- Enable [Caching](../building-apis/caching.md) for better performance
- Explore [GraphQL](../building-apis/graphql.md) for flexible queries

