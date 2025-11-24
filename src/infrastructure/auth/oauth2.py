"""OAuth2 authentication implementation."""

from typing import Any, Optional
from starlette.requests import Request
from authlib.integrations.starlette_client import OAuth

from src.infrastructure.auth.base import OAuth2Authentication
from src.domain.errors import AuthenticationError


class DefaultOAuth2Authentication(OAuth2Authentication):
    """Default OAuth2 authentication implementation."""

    def __init__(self, clientId: str, clientSecret: str, authorizationUrl: str, tokenUrl: str) -> None:
        """Initialize OAuth2 authentication.

        Args:
            clientId: OAuth2 client ID
            clientSecret: OAuth2 client secret
            authorizationUrl: OAuth2 authorization URL
            tokenUrl: OAuth2 token URL
        """
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.authorizationUrl = authorizationUrl
        self.tokenUrl = tokenUrl
        self.oauth = OAuth()

    async def authenticate(self, request: Request) -> Optional[dict[str, Any]]:
        """Authenticate using OAuth2.

        Args:
            request: Starlette request object

        Returns:
            User data dictionary if authenticated, None otherwise
        """
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return None

        try:
            accessToken = token.split(" ")[1]
            userInfo = await self.oauth.getUserInfo(accessToken)
            return userInfo
        except Exception as e:
            raise AuthenticationError(f"OAuth2 authentication failed: {e}") from e

