# Caching

Pylight integrates with Redis to provide efficient caching for API responses, improving performance and reducing database load.

## Overview

Pylight caching provides:

- **Redis Integration**: Fast in-memory caching
- **Automatic Cache Management**: Cache invalidation on updates
- **Per-Method Caching**: Cache specific HTTP methods
- **Configurable Expiration**: Set cache TTL per endpoint

## Basic Setup

### Redis Installation

Start Redis (using Docker):

```bash
docker run -d -p 6379:6379 redis:latest
```

Or install locally:

```bash
# macOS
brew install redis
redis-server

# Linux
apt-get install redis-server
redis-server
```

### Configuration

Enable caching in YAML:

```yaml
tables:
  - name: "products"
    features:
      caching:
        enabled: true
```

Or programmatically:

```python
from pylight.infrastructure.cache.redis import DefaultRedisCache

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    class Configuration:
        caching_class = DefaultRedisCache
        caching_method_names = ["GET"]  # Cache GET requests
```

## Cache Configuration

### Redis URL

Default Redis URL: `redis://localhost:6379`

Custom Redis URL:

```python
app = LightApi(
    databaseUrl="sqlite:///app.db",
    redisUrl="redis://localhost:6379/0"
)
```

### Cache Expiration

Set cache TTL (time to live):

```python
class Product(RestEndpoint):
    class Configuration:
        caching_class = DefaultRedisCache
        caching_method_names = ["GET"]
        cache_expiration_seconds = 3600  # 1 hour
```

## Caching Behavior

### GET Requests

GET requests are cached by default when caching is enabled:

```bash
# First request - hits database
GET /api/products

# Subsequent requests - served from cache
GET /api/products
```

### Cache Invalidation

Cache is automatically invalidated when:

- **POST**: New item created
- **PUT**: Item updated
- **DELETE**: Item deleted

### Cache Keys

Cache keys are generated based on:
- Table name
- HTTP method
- Query parameters (for filtering/sorting)

Example cache key: `products:GET:page=1&limit=10`

## Advanced Configuration

### Per-Method Caching

Cache only specific methods:

```yaml
tables:
  - name: "products"
    features:
      caching:
        enabled: true
        methods: ["GET"]  # Only cache GET requests
```

### Selective Caching

Cache only specific endpoints:

```python
class Product(RestEndpoint):
    class Configuration:
        caching_method_names = ["GET"]  # Only GET, not POST/PUT/DELETE
```

### Custom Cache Prefix

```python
class CustomCache(DefaultRedisCache):
    def __init__(self, redisUrl: str):
        super().__init__(redisUrl)
        self.prefix = "myapp:"  # Custom prefix
```

## Cache Management

### Manual Cache Clearing

```python
from pylight.infrastructure.cache.redis import DefaultRedisCache

cache = DefaultRedisCache("redis://localhost:6379")
await cache.flush()  # Clear all cache
```

### Cache Statistics

Monitor cache performance:

```python
# Check cache hit rate
# Monitor Redis metrics
redis-cli INFO stats
```

## Best Practices

1. **Cache Read-Heavy Endpoints**: Cache GET requests for frequently accessed data
2. **Set Appropriate TTL**: Balance freshness with performance
3. **Monitor Cache Hit Rate**: Track cache effectiveness
4. **Use Cache Warming**: Pre-populate cache for critical data
5. **Handle Cache Failures**: Gracefully degrade if Redis is unavailable

## Performance Considerations

### Cache Hit Rate

Aim for 80%+ cache hit rate for optimal performance.

### Memory Usage

Monitor Redis memory usage:

```bash
redis-cli INFO memory
```

### Cache Warming

Pre-populate cache on startup:

```python
async def warm_cache():
    # Pre-fetch frequently accessed data
    products = await get_popular_products()
    for product in products:
        await cache.set(f"product:{product.id}", product)
```

## Troubleshooting

### Cache Not Working

1. Verify Redis is running: `redis-cli ping`
2. Check Redis URL configuration
3. Verify caching is enabled for the table
4. Check cache expiration settings

### High Memory Usage

1. Reduce cache TTL
2. Limit cached endpoints
3. Use Redis eviction policies
4. Monitor cache size

## Examples

For complete caching examples, see:
- [Features Config Example](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/features_config.yaml)
- [Use Cases](../use-cases/index.md) for real-world patterns

## Next Steps

- Learn about [Pagination, Filtering, and Sorting](pagination-filtering-sorting.md)
- Explore [YAML Configuration](yaml-configuration.md) for complex setups
- Check out [Custom Caching](../customization/custom-caching.md) for advanced use cases

