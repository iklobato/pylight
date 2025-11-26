# Custom Caching

Pylight allows you to implement custom cache backends by extending the base cache classes.

## Overview

You can customize caching by:

- **Extending Redis Cache**: Add custom caching logic
- **Creating New Backends**: Implement completely custom cache backends
- **Custom Cache Strategies**: Implement custom cache invalidation strategies

## Extending Redis Cache

### Basic Extension

```python
from pylight.infrastructure.cache.redis import DefaultRedisCache
from typing import Any, Optional

class CustomRedisCache(DefaultRedisCache):
    """Custom Redis cache with additional features."""
    
    async def get(self, key: str) -> Optional[Any]:
        """Get with custom processing."""
        value = await super().get(key)
        if value:
            # Custom processing
            return self.process_value(value)
        return None
    
    def process_value(self, value: Any) -> Any:
        """Process cached value."""
        # Custom processing logic
        return value
```

## Creating New Cache Backend

### Implementing Base Interface

```python
from pylight.infrastructure.cache.base import Cache
from typing import Any, Optional

class MemoryCache(Cache):
    """In-memory cache implementation."""
    
    def __init__(self):
        self.cache: dict[str, Any] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, expirationSeconds: Optional[int] = None) -> None:
        """Set value in cache."""
        self.cache[key] = value
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self.cache.pop(key, None)
    
    async def flush(self) -> None:
        """Flush all cache entries."""
        self.cache.clear()
```

## Using Custom Cache

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint

class Product(RestEndpoint):
    class Configuration:
        caching_class = CustomRedisCache
        caching_method_names = ["GET"]
```

## Best Practices

1. **Implement All Methods**: Ensure all required methods are implemented
2. **Handle Errors**: Gracefully handle cache failures
3. **Set Expiration**: Always set appropriate expiration times
4. **Monitor Performance**: Track cache hit rates

## Next Steps

- Learn about [Caching](../building-apis/caching.md) for basic usage
- Explore [Middleware](middleware.md) for request handling

