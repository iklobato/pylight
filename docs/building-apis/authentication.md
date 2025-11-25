# Authentication

Pylight supports JWT and OAuth2 authentication out of the box, with role-based access control for fine-grained permissions.

## Overview

Pylight provides:

- **JWT Authentication**: Token-based authentication with role support
- **OAuth2 Authentication**: OAuth2 provider integration
- **Role-Based Access Control**: Control access per HTTP method and role
- **Per-Table Configuration**: Configure authentication per table

## JWT Authentication

### Basic Setup

Configure JWT authentication in your YAML file:

```yaml
authentication:
  jwt:
    secret_key: "your-secret-key-change-in-production"

tables:
  - name: "products"
    authentication:
      required: true
    permissions:
      GET: []  # Any authenticated user
      POST: ["admin"]
      PUT: ["admin"]
      DELETE: ["admin"]
```

[View source: `docs/examples/yaml_configs/auth_config.yaml`](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/auth_config.yaml)

### Programmatic Setup

```python
from src.presentation.app import LightApi
from src.domain.entities.rest_endpoint import RestEndpoint
from src.infrastructure.auth.jwt import DefaultJWTAuthentication
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    class Configuration:
        authentication_class = DefaultJWTAuthentication
        required_roles = {
            "GET": [],  # Any authenticated user
            "POST": ["admin"],
            "PUT": ["admin"],
            "DELETE": ["admin"]
        }

app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
app.run(host="localhost", port=8000)
```

### Generating JWT Tokens

To generate JWT tokens for testing:

```python
import jwt
import datetime

secret_key = "your-secret-key"
payload = {
    "username": "admin",
    "role": "admin",
    "sub": "admin",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
}
token = jwt.encode(payload, secret_key, algorithm="HS256")
print(f"Bearer {token}")
```

### Using JWT Tokens

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/products
```

## OAuth2 Authentication

### Basic Setup

Configure OAuth2 authentication:

```yaml
authentication:
  oauth2:
    client_id: "your-oauth-client-id"
    client_secret: "your-oauth-client-secret"
    authorization_url: "https://oauth-provider.com/authorize"
    token_url: "https://oauth-provider.com/token"

tables:
  - name: "products"
    authentication:
      required: true
```

### Programmatic Setup

```python
from src.infrastructure.auth.oauth2 import DefaultOAuth2Authentication

class Product(RestEndpoint):
    class Configuration:
        authentication_class = DefaultOAuth2Authentication(
            clientId="your-client-id",
            clientSecret="your-client-secret",
            authorizationUrl="https://oauth-provider.com/authorize",
            tokenUrl="https://oauth-provider.com/token"
        )
```

## Role-Based Access Control

### Permission Configuration

Control access per HTTP method and role:

```yaml
tables:
  - name: "products"
    permissions:
      GET: []              # Any authenticated user
      POST: ["admin"]      # Only admin role
      PUT: ["admin", "editor"]  # Admin or editor roles
      DELETE: ["admin"]    # Only admin role
```

### Public Access

Allow public access (no authentication):

```yaml
tables:
  - name: "public_data"
    authentication:
      required: false  # No authentication required
```

### Mixed Access

Different methods require different authentication:

```yaml
tables:
  - name: "products"
    authentication:
      required: true  # Authentication required for this table
    permissions:
      GET: []          # Public read access
      POST: ["user"]    # Authenticated users can create
      PUT: ["admin"]    # Only admins can update
      DELETE: ["admin"] # Only admins can delete
```

## Custom Authentication

Extend the base authentication classes for custom logic:

```python
from src.infrastructure.auth.jwt import DefaultJWTAuthentication
from starlette.requests import Request

class CustomJWTAuthentication(DefaultJWTAuthentication):
    async def authenticate(self, request: Request):
        # Custom authentication logic
        user = await super().authenticate(request)
        if user:
            # Additional validation
            if user.get("role") == "banned":
                return None
        return user
```

## Authentication Flow

1. **Request arrives** with Authorization header
2. **Authentication middleware** extracts token
3. **Authentication class** validates token
4. **User data** extracted (username, role)
5. **Permission check** validates role against required roles
6. **Request proceeds** if authorized, otherwise 401/403

## Error Responses

### 401 Unauthorized

No token or invalid token:

```json
{
  "error": "Authentication required",
  "detail": "Invalid or missing JWT token"
}
```

### 403 Forbidden

Valid token but insufficient permissions:

```json
{
  "error": "Insufficient permissions",
  "detail": "Role 'user' does not have permission for POST"
}
```

## Best Practices

1. **Use Strong Secret Keys**: Generate random, secure secret keys for JWT
2. **Set Token Expiration**: Always set expiration times for tokens
3. **Use HTTPS**: Always use HTTPS in production
4. **Validate Roles**: Always validate roles on the server side
5. **Least Privilege**: Grant minimum required permissions

## Examples

For complete authentication examples, see:
- [Authentication Config Example](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/auth_config.yaml)
- [Use Cases](../use-cases/authenticated-api.md) for authenticated API examples

## Next Steps

- Learn about [Caching](caching.md) for performance
- Explore [YAML Configuration](yaml-configuration.md) for complex setups
- Check out [Custom Authentication](../customization/custom-authentication.md) for advanced use cases

