"""Base Cache class."""

from typing import Any, Optional


class Cache:
    """Base class for caching implementations."""

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        raise NotImplementedError("Subclasses must implement get method")

    async def set(self, key: str, value: Any, expirationSeconds: Optional[int] = None) -> None:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expirationSeconds: Optional expiration time in seconds
        """
        raise NotImplementedError("Subclasses must implement set method")

    async def delete(self, key: str) -> None:
        """Delete a value from cache.

        Args:
            key: Cache key
        """
        raise NotImplementedError("Subclasses must implement delete method")

    async def flush(self) -> None:
        """Flush all cache entries."""
        raise NotImplementedError("Subclasses must implement flush method")


class RedisCache(Cache):
    """Base class for Redis cache implementations."""

    prefix: str = "cache:"
    expirationSeconds: int = 3600

    def __init__(self, redisUrl: str) -> None:
        """Initialize Redis cache.

        Args:
            redisUrl: Redis connection URL
        """
        self.redisUrl = redisUrl

