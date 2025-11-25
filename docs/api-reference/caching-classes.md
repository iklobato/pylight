# Caching Classes

Documentation for caching classes in Pylight.

## DefaultRedisCache

Default Redis cache implementation.

### Class Definition

```python
class DefaultRedisCache(RedisCache):
    """Default Redis cache implementation."""
```

### Constructor

```python
def __init__(self, redisUrl: str) -> None
```

**Parameters**:
- `redisUrl` (str): Redis connection URL

### Methods

#### `connect`

Connect to Redis.

```python
async def connect(self) -> None
```

**Raises**:
- `ConfigurationError`: If connection fails

#### `get`

Get a value from cache.

```python
async def get(self, key: str) -> Optional[Any]
```

**Parameters**:
- `key` (str): Cache key

**Returns**:
- `Optional[Any]`: Cached value or None

#### `set`

Set a value in cache.

```python
async def set(
    self,
    key: str,
    value: Any,
    expirationSeconds: Optional[int] = None
) -> None
```

**Parameters**:
- `key` (str): Cache key
- `value` (Any): Value to cache
- `expirationSeconds` (Optional[int]): Expiration time in seconds

#### `delete`

Delete a value from cache.

```python
async def delete(self, key: str) -> None
```

**Parameters**:
- `key` (str): Cache key

#### `flush`

Flush all cache entries.

```python
async def flush(self) -> None
```

## Next Steps

- Learn about [Caching](../building-apis/caching.md) for usage
- Explore [Custom Caching](../customization/custom-caching.md) for customization

