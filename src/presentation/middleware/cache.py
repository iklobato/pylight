"""Caching middleware."""

from typing import Any, List, Optional
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
import json

from src.presentation.middleware.base import Middleware
from src.infrastructure.cache.base import Cache


class CacheMiddleware(Middleware):
    """Middleware for caching responses."""

    def __init__(
        self,
        cacheClass: Optional[type[Cache]] = None,
        cacheMethods: List[str] = ["GET"],
        ttl: int = 300,
    ) -> None:
        """Initialize cache middleware.

        Args:
            cacheClass: Cache class to use
            cacheMethods: HTTP methods to cache
            ttl: Time to live in seconds (default: 300)
        """
        self.cacheClass = cacheClass
        self.cacheMethods = cacheMethods
        self.ttl = ttl

    def _generateCacheKey(self, request: Request, modelName: str, resourceId: Optional[str] = None) -> str:
        """Generate cache key for request.

        Args:
            request: Starlette request object
            modelName: Model name
            resourceId: Optional resource ID

        Returns:
            Cache key string
        """
        if resourceId:
            return f"{modelName}:{resourceId}"
        else:
            # Include sort, page, and limit in cache key since different sorts/pages should have different cache entries
            filterParams = "&".join(
                f"{k}={v}" for k, v in sorted(request.query_params.items())
            )
            return f"{modelName}:list:{filterParams}" if filterParams else f"{modelName}:list"

    async def getCachedResponse(self, request: Request, modelName: str, resourceId: Optional[str] = None) -> Optional[JSONResponse]:
        """Get cached response if available.

        Args:
            request: Starlette request object
            modelName: Model name
            resourceId: Optional resource ID

        Returns:
            Cached JSONResponse or None
        """
        if not self.cacheClass or request.method not in self.cacheMethods:
            return None

        try:
            cache = self.cacheClass()
            cacheKey = self._generateCacheKey(request, modelName, resourceId)
            cachedValue = await cache.get(cacheKey)

            if cachedValue:
                if isinstance(cachedValue, str):
                    try:
                        data = json.loads(cachedValue)
                    except json.JSONDecodeError:
                        data = cachedValue
                else:
                    data = cachedValue

                return JSONResponse(data, status_code=200)
        except Exception:
            pass

        return None

    async def setCachedResponse(
        self,
        request: Request,
        modelName: str,
        response: Response,
        resourceId: Optional[str] = None,
    ) -> None:
        """Cache response.

        Args:
            request: Starlette request object
            modelName: Model name
            response: Response to cache
            resourceId: Optional resource ID
        """
        if not self.cacheClass or request.method not in self.cacheMethods:
            return

        try:
            cache = self.cacheClass()
            cacheKey = self._generateCacheKey(request, modelName, resourceId)

            if isinstance(response, JSONResponse):
                body = response.body
                if isinstance(body, bytes):
                    body = body.decode("utf-8")
                await cache.set(cacheKey, body, self.ttl)
        except Exception:
            pass

    async def invalidateCache(self, modelName: str, resourceId: Optional[str] = None) -> None:
        """Invalidate cache entries.

        Args:
            modelName: Model name
            resourceId: Optional resource ID to invalidate specific resource
        """
        if not self.cacheClass:
            return

        try:
            cache = self.cacheClass()
            if resourceId:
                cacheKey = f"{modelName}:{resourceId}"
                await cache.delete(cacheKey)
            cacheKey = f"{modelName}:list"
            await cache.delete(cacheKey)
        except Exception:
            pass

    async def process(self, request: Request, response: Optional[Response] = None) -> Optional[Response]:
        """Process caching."""
        return response

