"""Authentication middleware."""

from typing import Any, Optional, Type
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.presentation.middleware.base import Middleware
from src.infrastructure.auth.base import Authentication
from src.domain.errors import AuthenticationError, AuthorizationError


class AuthenticationMiddleware(Middleware):
    """Middleware for authentication."""

    def __init__(
        self,
        authenticationClass: Optional[Type[Authentication]] = None,
        requiredRoles: Optional[list[str]] = None,
    ) -> None:
        """Initialize authentication middleware.

        Args:
            authenticationClass: Authentication class to use
            requiredRoles: List of required roles (None means any authenticated user)
        """
        self.authenticationClass = authenticationClass
        self.requiredRoles = requiredRoles or []

    async def process(self, request: Request, response: Optional[Response] = None) -> Optional[Response]:
        """Process authentication.

        Args:
            request: Starlette request object
            response: Optional response (not used in authentication middleware)

        Returns:
            JSONResponse with 401 if authentication fails, 403 if authorization fails, None if successful
        """
        if not self.authenticationClass:
            return None

        try:
            auth = self.authenticationClass()
            user = await auth.authenticate(request)

            if not user:
                return JSONResponse(
                    {"error": "Authentication required"},
                    status_code=401
                )

            if self.requiredRoles:
                userRole = user.get("role")
                if not userRole or userRole not in self.requiredRoles:
                    return JSONResponse(
                        {"error": "Insufficient permissions"},
                        status_code=403
                    )

            request.state.user = user
            return None

        except AuthenticationError as e:
            return JSONResponse(
                {"error": "Authentication failed", "detail": str(e)},
                status_code=401
            )
        except AuthorizationError as e:
            return JSONResponse(
                {"error": "Authorization failed", "detail": str(e)},
                status_code=403
            )
        except Exception as e:
            return JSONResponse(
                {"error": "Authentication error", "detail": str(e)},
                status_code=500
            )

