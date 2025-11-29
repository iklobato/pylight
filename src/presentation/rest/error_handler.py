"""Error handling infrastructure."""

from typing import Any
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.exceptions import HTTPException

from src.domain.errors import (
    PylightError,
    ValidationError,
    ConfigurationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
)


async def handleError(request: Request, exc: Exception) -> Response:
    """Handle exceptions and return appropriate HTTP responses.

    Args:
        request: Starlette request object
        exc: Exception to handle

    Returns:
        JSON response with error details
    """
    if isinstance(exc, HTTPException):
        return JSONResponse(
            {"error": exc.detail, "status_code": exc.status_code},
            status_code=exc.status_code,
        )

    if isinstance(exc, ValidationError):
        # Check if ValidationError has field-level errors
        if hasattr(exc, 'field_errors') and exc.field_errors:
            # Return structured field-level error format
            return JSONResponse(
                {
                    "error": "Validation failed",
                    "errors": exc.field_errors,
                    "status_code": 400
                },
                status_code=400,
            )
        else:
            # Single error message (backward compatibility)
            return JSONResponse(
                {"error": "Validation failed", "detail": str(exc), "status_code": 400},
                status_code=400,
            )

    if isinstance(exc, AuthenticationError):
        return JSONResponse(
            {"error": "Authentication failed", "detail": str(exc), "status_code": 401},
            status_code=401,
        )

    if isinstance(exc, AuthorizationError):
        return JSONResponse(
            {"error": "Authorization failed", "detail": str(exc), "status_code": 403},
            status_code=403,
        )

    if isinstance(exc, ConfigurationError):
        return JSONResponse(
            {"error": "Configuration error", "detail": str(exc), "status_code": 500},
            status_code=500,
        )

    if isinstance(exc, DatabaseError):
        return JSONResponse(
            {"error": "Database error", "detail": str(exc), "status_code": 500},
            status_code=500,
        )

    if isinstance(exc, NotFoundError):
        return JSONResponse(
            {"error": "Resource not found", "detail": str(exc), "status_code": 404},
            status_code=404,
        )

    if isinstance(exc, PylightError):
        return JSONResponse(
            {"error": "Framework error", "detail": str(exc), "status_code": 500},
            status_code=500,
        )

    return JSONResponse(
        {"error": "Internal server error", "detail": str(exc), "status_code": 500},
        status_code=500,
    )

