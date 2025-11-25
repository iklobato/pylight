# GraphQL

Pylight automatically generates GraphQL schemas and resolvers for your models, providing a flexible query interface alongside REST endpoints.

## Overview

When you register a model, Pylight automatically creates:

- **GraphQL Queries**: Query your data with flexible field selection
- **GraphQL Mutations**: Create, update, and delete operations
- **GraphiQL Interface**: Interactive GraphQL explorer at `/graphiql`
- **GraphQL Endpoint**: Available at `/graphql`

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

This automatically creates GraphQL queries and mutations for the `products` table.

## GraphQL Queries

### List All Items

```graphql
query {
  products {
    id
    name
    price
  }
}
```

Response:

```json
{
  "data": {
    "products": [
      {
        "id": 1,
        "name": "Laptop",
        "price": 999
      },
      {
        "id": 2,
        "name": "Mouse",
        "price": 29
      }
    ]
  }
}
```

### Get Single Item

```graphql
query {
  product(id: 1) {
    id
    name
    price
  }
}
```

### Filtering

```graphql
query {
  products(filter: {price: {gt: 100}}) {
    id
    name
    price
  }
}
```

Filter operators:
- `eq`: Equals
- `ne`: Not equals
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `like`: Pattern matching
- `in`: Value in list

### Sorting

```graphql
query {
  products(sort: "-price") {
    id
    name
    price
  }
}
```

Use `-` prefix for descending order.

### Pagination

```graphql
query {
  products(page: 1, limit: 10) {
    id
    name
    price
  }
}
```

## GraphQL Mutations

### Create Item

```graphql
mutation {
  createProduct(name: "Keyboard", price: 79) {
    id
    name
    price
  }
}
```

Response:

```json
{
  "data": {
    "createProduct": {
      "id": 3,
      "name": "Keyboard",
      "price": 79
    }
  }
}
```

### Update Item

```graphql
mutation {
  updateProduct(id: 1, name: "Updated Laptop", price: 1099) {
    id
    name
    price
  }
}
```

### Delete Item

```graphql
mutation {
  deleteProduct(id: 1) {
    id
  }
}
```

[View source: `docs/examples/graphql_queries.py`](https://github.com/iklobato/pylight/blob/main/docs/examples/graphql_queries.py)

## GraphiQL Interface

Access the interactive GraphQL explorer at:

```
http://localhost:8000/graphiql
```

GraphiQL provides:
- Interactive query editor
- Schema explorer
- Query history
- Auto-completion

## Field Selection

One of GraphQL's key features is flexible field selection:

```graphql
# Get only specific fields
query {
  products {
    id
    name
  }
}

# Get all fields
query {
  products {
    id
    name
    price
    description
    createdAt
  }
}
```

## Nested Queries

For relationships (when models have foreign keys):

```graphql
query {
  products {
    id
    name
    category {
      id
      name
    }
  }
}
```

## Authentication

To require authentication for GraphQL queries and mutations, see [Authentication](authentication.md).

## Caching

To enable caching for GraphQL queries, see [Caching](caching.md).

## Error Handling

GraphQL returns errors in a structured format:

```json
{
  "errors": [
    {
      "message": "Product not found",
      "path": ["product"],
      "extensions": {
        "code": "NOT_FOUND"
      }
    }
  ],
  "data": null
}
```

## Advanced Examples

For more complex GraphQL examples, see:
- [GraphQL Queries Example](https://github.com/iklobato/pylight/blob/main/docs/examples/graphql_queries.py)
- [Use Cases](../use-cases/index.md) for real-world patterns

## Next Steps

- Learn about [REST Endpoints](rest-endpoints.md) for traditional APIs
- Add [Authentication](authentication.md) to secure GraphQL
- Enable [Caching](caching.md) for better performance
- Explore [WebSocket](websocket.md) for real-time updates

