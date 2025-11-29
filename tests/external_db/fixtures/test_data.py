"""Test data definitions and constants."""

# Table names
TABLES = [
    "users",
    "categories",
    "products",
    "addresses",
    "orders",
    "order_items",
    "reviews",
    "payments",
    "shipments",
    "inventory"
]

# Test data volume requirements
RECORDS_PER_TABLE = {
    "users": 1000,
    "categories": 50,
    "products": 1000,
    "addresses": 2000,  # 2 per user
    "orders": 2000,
    "order_items": 5000,  # ~3 per order
    "reviews": 3000,
    "payments": 2000,  # 1 per order
    "shipments": 2000,  # 1 per order
    "inventory": 1000  # 1 per product
}

# Test endpoints
API_ENDPOINTS = {
    "list": "/api/{table_name}",
    "detail": "/api/{table_name}/{id}",
    "health": "/health",
    "docs": "/docs",
    "graphql": "/graphql",
    "graphiql": "/graphiql",
    "websocket": "/ws/{table_name}"
}

# Test filter operators
FILTER_OPERATORS = [
    "__eq",  # Equals
    "__ne",  # Not equals
    "__gt",  # Greater than
    "__gte", # Greater than or equal
    "__lt",  # Less than
    "__lte", # Less than or equal
    "__like", # Pattern matching
    "__in"   # Value in list
]

# Test sort directions
SORT_DIRECTIONS = ["asc", "desc"]

# Sample test data for creating records
SAMPLE_PRODUCT = {
    "name": "Test Product",
    "description": "Test product description",
    "sku": "TEST-SKU-001",
    "price": "99.99",
    "cost": "50.00",
    "brand": "Test Brand",
    "is_active": True
}

SAMPLE_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password_hash": "hashed_password",
    "first_name": "Test",
    "last_name": "User",
    "role": "user",
    "is_active": True
}

SAMPLE_ORDER = {
    "user_id": 1,
    "order_number": "TEST-ORD-001",
    "status": "pending",
    "subtotal": "100.00",
    "tax": "10.00",
    "shipping_cost": "5.00",
    "total": "115.00"
}

