# Custom Authentication

Pylight allows you to create custom authentication providers by extending the base authentication classes.

## Overview

You can customize authentication by:

- **Extending JWT Authentication**: Add custom JWT validation logic
- **Extending OAuth2 Authentication**: Customize OAuth2 flow
- **Creating New Providers**: Implement completely custom authentication

## Extending JWT Authentication

### Basic Extension

```python
from pylight.infrastructure.auth.jwt import DefaultJWTAuthentication
from starlette.requests import Request
from typing import Optional, Any

class CustomJWTAuthentication(DefaultJWTAuthentication):
    """Custom JWT authentication with additional validation."""
    
    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate with custom validation."""
        # Call parent authentication
        user = await super().authenticate(request)
        
        if user:
            # Add custom validation
            if user.get("role") == "banned":
                return None
            
            # Add custom user data
            user["custom_field"] = "custom_value"
        
        return user
```

### Using Custom Authentication

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    class Configuration:
        authentication_class = CustomJWTAuthentication
        required_roles = {
            "GET": [],
            "POST": ["admin"]
        }

app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
app.run(host="localhost", port=8000)
```

## Extending OAuth2 Authentication

### Custom OAuth2 Provider

```python
from pylight.infrastructure.auth.oauth2 import DefaultOAuth2Authentication
from starlette.requests import Request
from typing import Optional, Any

class CustomOAuth2Authentication(DefaultOAuth2Authentication):
    """Custom OAuth2 authentication with additional processing."""
    
    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate with custom OAuth2 processing."""
        user = await super().authenticate(request)
        
        if user:
            # Process user data
            user["provider"] = "custom_oauth2"
        
        return user
```

## Creating New Authentication Provider

### Implementing Base Interface

```python
from pylight.infrastructure.auth.base import Authentication
from starlette.requests import Request
from typing import Optional, Any

class CustomAuthentication(Authentication):
    """Custom authentication provider."""
    
    def __init__(self, api_key: str):
        """Initialize custom authentication."""
        self.api_key = api_key
    
    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate using custom method."""
        api_key = request.headers.get("X-API-Key")
        
        if api_key == self.api_key:
            return {
                "username": "api_user",
                "role": "user"
            }
        
        return None
```

## Advanced Examples

### Multi-Provider Authentication

Support multiple authentication methods:

```python
class MultiAuth(Authentication):
    """Support multiple authentication providers."""
    
    def __init__(self):
        self.jwt_auth = DefaultJWTAuthentication()
        self.oauth2_auth = DefaultOAuth2Authentication(...)
    
    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Try multiple authentication methods."""
        # Try JWT first
        user = await self.jwt_auth.authenticate(request)
        if user:
            return user
        
        # Try OAuth2
        user = await self.oauth2_auth.authenticate(request)
        if user:
            return user
        
        return None
```

### Token Refresh

Implement token refresh logic:

```python
class JWTAuthWithRefresh(DefaultJWTAuthentication):
    """JWT authentication with refresh token support."""
    
    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate with refresh token support."""
        user = await super().authenticate(request)
        
        if not user:
            # Try refresh token
            refresh_token = request.headers.get("X-Refresh-Token")
            if refresh_token:
                # Validate and refresh
                user = await self.refresh_token(refresh_token)
        
        return user
    
    async def refresh_token(self, refresh_token: str) -> Optional[dict[str, Any]]:
        """Refresh access token."""
        # Implementation
        pass
```

## Best Practices

1. **Extend Base Classes**: Extend existing classes when possible
2. **Handle Errors**: Gracefully handle authentication failures
3. **Validate Input**: Always validate authentication tokens/credentials
4. **Log Security Events**: Log authentication attempts and failures
5. **Test Thoroughly**: Test all authentication paths

## Examples

For complete authentication examples, see:
- [Authentication Documentation](../building-apis/authentication.md)
- [Use Cases](../use-cases/authenticated-api.md)

## Next Steps

- Learn about [Custom Caching](custom-caching.md)
- Explore [Middleware](middleware.md) for request handling
- Check out [Error Handling](error-handling.md) for error customization

