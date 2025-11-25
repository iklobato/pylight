# Middleware

Pylight supports custom middleware for cross-cutting concerns like logging, authentication, CORS, and more.

## Overview

Middleware allows you to:

- **Process Requests**: Intercept and process requests before handlers
- **Process Responses**: Modify responses before sending
- **Add Headers**: Add custom headers to responses
- **Logging**: Log requests and responses
- **Error Handling**: Handle errors globally

## Basic Middleware

### Starlette Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Process request
        print(f"Request: {request.method} {request.url}")
        
        # Call next middleware/handler
        response = await call_next(request)
        
        # Process response
        print(f"Response: {response.status_code}")
        
        return response
```

## Adding Middleware

### Programmatic Addition

```python
from src.presentation.app import LightApi

app = LightApi(databaseUrl="sqlite:///app.db")
app.addMiddleware([LoggingMiddleware])
app.run(host="localhost", port=8000)
```

## Common Middleware Patterns

### CORS Middleware

```python
from starlette.middleware.cors import CORSMiddleware

app = LightApi(databaseUrl="sqlite:///app.db")
app.starletteApp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Authentication Middleware

```python
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check authentication
        if not await self.is_authenticated(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        return await call_next(request)
```

## Best Practices

1. **Order Matters**: Middleware order affects execution
2. **Handle Errors**: Always handle errors gracefully
3. **Performance**: Keep middleware lightweight
4. **Logging**: Log important events

## Next Steps

- Learn about [Error Handling](error-handling.md)
- Explore [Deployment](deployment.md) for production setup

