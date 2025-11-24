"""CORS middleware."""

from typing import List, Optional
from starlette.requests import Request
from starlette.responses import Response

from src.presentation.middleware.base import Middleware


class CORSMiddleware(Middleware):
    """CORS middleware implementation."""

    def __init__(self, allowedOrigins: List[str] = ["*"]) -> None:
        """Initialize CORS middleware.

        Args:
            allowedOrigins: List of allowed origins
        """
        self.allowedOrigins = allowedOrigins

    async def process(self, request: Request, response: Optional[Response] = None) -> Optional[Response]:
        """Process CORS headers."""
        if response:
            origin = request.headers.get("origin")
            if origin and (origin in self.allowedOrigins or "*" in self.allowedOrigins):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

