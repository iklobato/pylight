# REST Endpoints

Pylight automatically generates REST endpoints (GET, POST, PUT, DELETE) for your models. This guide covers everything you need to know about REST endpoints in Pylight.

## Overview

When you register a model with Pylight, it automatically creates REST endpoints for all CRUD operations:

- `GET /api/{table_name}` - List all items (with pagination, filtering, sorting)
- `GET /api/{table_name}/{id}` - Get a specific item
- `POST /api/{table_name}` - Create a new item
- `PUT /api/{table_name}/{id}` - Update an item
- `DELETE /api/{table_name}/{id}` - Delete an item

## Basic Example

Define a model and register it:

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

[View source: `docs/examples/basic_usage.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/basic_usage.py)

This automatically creates all REST endpoints for the `products` table.

## List Endpoints (GET /api/{table_name})

List all items with optional pagination, filtering, and sorting.

### Basic List

```bash
GET /api/products
```

Response:

```json
{
  "items": [
    {"id": 1, "name": "Laptop", "price": 999},
    {"id": 2, "name": "Mouse", "price": 29}
  ],
  "total": 2,
  "page": 1,
  "limit": 10
}
```

### Pagination

```bash
GET /api/products?page=1&limit=10
```

Query Parameters:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)

### Filtering

Filter by field values:

```bash
GET /api/products?price__gt=100
GET /api/products?name__like=laptop
GET /api/products?price__gte=50&price__lte=200
```

Filter Operators:
- `__eq`: Equals
- `__ne`: Not equals
- `__gt`: Greater than
- `__gte`: Greater than or equal
- `__lt`: Less than
- `__lte`: Less than or equal
- `__like`: Pattern matching (SQL LIKE)
- `__in`: Value in list

### Sorting

```bash
GET /api/products?sort=price
GET /api/products?sort=-price
GET /api/products?sort=name,price
```

- Prefix with `-` for descending order
- Multiple fields: comma-separated

### Combined Query

```bash
GET /api/products?page=1&limit=20&price__gt=100&sort=-price
```

## Get Single Item (GET /api/{table_name}/{id})

Retrieve a specific item by ID:

```bash
GET /api/products/1
```

Response:

```json
{
  "id": 1,
  "name": "Laptop",
  "price": 999
}
```

## Create Item (POST /api/{table_name})

Create a new item:

```bash
POST /api/products
Content-Type: application/json

{
  "name": "Keyboard",
  "price": 79
}
```

Response (201 Created):

```json
{
  "id": 3,
  "name": "Keyboard",
  "price": 79
}
```

[View source: `docs/examples/rest_endpoints.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/rest_endpoints.py)

## Update Item (PUT /api/{table_name}/{id})

Update an existing item:

```bash
PUT /api/products/1
Content-Type: application/json

{
  "name": "Updated Laptop",
  "price": 1099
}
```

Response (200 OK):

```json
{
  "id": 1,
  "name": "Updated Laptop",
  "price": 1099
}
```

## Delete Item (DELETE /api/{table_name}/{id})

Delete an item:

```bash
DELETE /api/products/1
```

Response: 200 OK or 204 No Content

## Response Formats

### Success Responses

- **200 OK**: Successful GET, PUT, DELETE
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE (some implementations)

### Error Responses

- **400 Bad Request**: Invalid request data
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

Error response format:

```json
{
  "error": "Error message",
  "detail": "Additional error details"
}
```

## Method Restrictions

You can restrict which HTTP methods are available for a model:

```python
class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    class Configuration:
        # Only allow GET and POST
        allowed_methods = ["GET", "POST"]
```

Or via YAML configuration:

```yaml
tables:
  - name: products
    methods: ["GET", "POST"]
```

## Authentication

To require authentication for REST endpoints, see [Authentication](authentication.md).

## Caching

To enable caching for GET requests, see [Caching](caching.md).

## Advanced Examples

For more complex REST endpoint examples, see:
- [REST Endpoints Example](https://github.com/iklobato/pylight/blob/main/docs/examples/rest_endpoints.py)
- [Use Cases](../use-cases/index.md) for real-world patterns

## Next Steps

- Learn about [GraphQL](graphql.md) for flexible queries
- Add [Authentication](authentication.md) to secure endpoints
- Enable [Caching](caching.md) for better performance
- Configure via [YAML Configuration](yaml-configuration.md)

