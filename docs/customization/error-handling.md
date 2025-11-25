# Error Handling

Pylight provides comprehensive error handling with customizable error responses.

## Overview

Pylight handles errors at multiple levels:

- **Domain Errors**: Business logic errors
- **Configuration Errors**: Configuration validation errors
- **Database Errors**: Database connection and query errors
- **Authentication Errors**: Authentication and authorization errors

## Error Types

### ConfigurationError

Raised when configuration is invalid:

```python
from src.domain.errors import ConfigurationError

raise ConfigurationError("Invalid database URL")
```

### DatabaseError

Raised when database operations fail:

```python
from src.domain.errors import DatabaseError

raise DatabaseError("Failed to connect to database")
```

### AuthenticationError

Raised when authentication fails:

```python
from src.domain.errors import AuthenticationError

raise AuthenticationError("Invalid credentials")
```

## Custom Error Handlers

### Global Error Handler

```python
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException

async def custom_error_handler(request, exc):
    """Custom error handler."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            {"error": exc.detail, "status_code": exc.status_code},
            status_code=exc.status_code
        )
    return JSONResponse(
        {"error": "Internal server error"},
        status_code=500
    )

app.starletteApp.add_exception_handler(Exception, custom_error_handler)
```

## Error Response Format

Standard error response:

```json
{
  "error": "Error message",
  "detail": "Additional error details"
}
```

## Best Practices

1. **Use Appropriate Error Types**: Use specific error types
2. **Provide Clear Messages**: Error messages should be clear and actionable
3. **Log Errors**: Always log errors for debugging
4. **Don't Expose Internals**: Don't expose internal implementation details

## Next Steps

- Learn about [Deployment](deployment.md) for production error handling
- Explore [Troubleshooting](../troubleshooting/index.md) for common issues

