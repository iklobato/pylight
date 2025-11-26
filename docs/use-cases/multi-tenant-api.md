# Multi-Tenant API

Complete example of creating a multi-tenant API with tenant isolation.

## Overview

This use case demonstrates:
- Tenant identification
- Tenant-based data filtering
- Custom middleware for tenant handling

## Step 1: Define Model with Tenant

```python
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(100))  # Tenant identifier
    name = Column(String(100))
    price = Column(Integer)
```

## Step 2: Create Tenant Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from header
        tenant_id = request.headers.get("X-Tenant-ID")
        request.state.tenant_id = tenant_id
        return await call_next(request)
```

## Step 3: Filter by Tenant

Customize REST handlers to filter by tenant:

```python
# In custom REST handler
async def get_handler(request):
    tenant_id = request.state.tenant_id
    # Filter products by tenant_id
    products = await session.query(Product).filter(
        Product.tenant_id == tenant_id
    ).all()
    return products
```

## Testing

### Request with Tenant

```bash
curl -H "X-Tenant-ID: tenant1" \
     http://localhost:8000/api/products
```

Only returns products for tenant1.

## Next Steps

- Learn about [Middleware](../customization/middleware.md) for details
- Explore [Customization](../customization/index.md) for advanced patterns

