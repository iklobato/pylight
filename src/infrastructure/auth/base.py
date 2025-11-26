"""Base Authentication class."""

from typing import Any, Optional
from starlette.requests import Request


class Authentication:
    """Base class for authentication implementations."""

    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate a request.

        Args:
            request: Starlette request object

        Returns:
            User data dictionary if authenticated, None otherwise
        """
        raise NotImplementedError("Subclasses must implement authenticate method")


class JWTAuthentication(Authentication):
    """Base class for JWT authentication."""

    def __init__(self, secretKey: str, allowlist: list[str] | None = None) -> None:
        """Initialize JWT authentication.

        Args:
            secretKey: Secret key for JWT token verification (HS256)
            allowlist: Algorithm allowlist (default: ["HS256"])
        """
        self.secretKey = secretKey
        self.allowlist = allowlist if allowlist is not None else ["HS256"]

    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate using JWT token from Authorization header."""
        raise NotImplementedError("Subclasses must implement authenticate method")


class OAuth2Authentication(Authentication):
    """Base class for OAuth2 authentication."""

    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate using OAuth2."""
        raise NotImplementedError("Subclasses must implement authenticate method")

