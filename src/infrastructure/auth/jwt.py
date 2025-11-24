"""JWT authentication implementation."""

from typing import Any, Optional
from starlette.requests import Request
import jwt

from src.infrastructure.auth.base import JWTAuthentication
from src.domain.errors import AuthenticationError


class DefaultJWTAuthentication(JWTAuthentication):
    """Default JWT authentication implementation with role support."""

    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate using JWT token from Authorization header.

        Args:
            request: Starlette request object

        Returns:
            User data dictionary with username and role if authenticated, None otherwise
        """
        authHeader = request.headers.get("Authorization")
        if not authHeader or not authHeader.startswith("Bearer "):
            return None

        token = authHeader.split(" ")[1]
        try:
            payload = jwt.decode(token, self.secretKey, algorithms=["HS256"])
            return {
                "username": payload.get("username"),
                "role": payload.get("role"),
                "sub": payload.get("sub"),
            }
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid JWT token")

