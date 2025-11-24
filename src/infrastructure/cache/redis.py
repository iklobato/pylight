"""Redis cache implementation."""

from typing import Any, Optional
import redis.asyncio as redis

from src.infrastructure.cache.base import RedisCache
from src.domain.errors import ConfigurationError


class DefaultRedisCache(RedisCache):
    """Default Redis cache implementation."""

    def __init__(self, redisUrl: str) -> None:
        """Initialize Redis cache.

        Args:
            redisUrl: Redis connection URL
        """
        super().__init__(redisUrl)
        self.client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = await redis.from_url(self.redisUrl, decode_responses=True)
        except Exception as e:
            raise ConfigurationError(f"Failed to connect to Redis: {e}") from e

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.client:
            await self.connect()
        if self.client:
            value = await self.client.get(f"{self.prefix}{key}")
            return value
        return None

    async def set(self, key: str, value: Any, expirationSeconds: Optional[int] = None) -> None:
        """Set a value in cache."""
        if not self.client:
            await self.connect()
        if self.client:
            exp = expirationSeconds or self.expirationSeconds
            await self.client.setex(f"{self.prefix}{key}", exp, str(value))

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        if not self.client:
            await self.connect()
        if self.client:
            await self.client.delete(f"{self.prefix}{key}")

    async def flush(self) -> None:
        """Flush all cache entries."""
        if not self.client:
            await self.connect()
        if self.client:
            keys = await self.client.keys(f"{self.prefix}*")
            if keys:
                await self.client.delete(*keys)

