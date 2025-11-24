"""Base Middleware class."""

from typing import Any, Optional
from starlette.requests import Request
from starlette.responses import Response


class Middleware:
    """Base class for middleware implementations."""

    async def process(self, request: Request, response: Optional[Response] = None) -> Optional[Response]:
        """Process a request or response.

        Args:
            request: Starlette request object
            response: Optional response object (for response middleware)

        Returns:
            Response object if processing should stop, None to continue
        """
        if response:
            return response
        return None

