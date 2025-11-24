"""REST PUT endpoint handler."""

from typing import Any, Optional, Type
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ValidationError
from src.infrastructure.database.connection import DatabaseManager
from src.presentation.middleware.auth import AuthenticationMiddleware
from src.presentation.middleware.cache import CacheMiddleware
from src.presentation.websocket.handler import getWebSocketManager
from src.shared.serialization.serializer import serializeModel


def putHandler(model: Type[RestEndpoint], databaseManager: Optional[DatabaseManager] = None) -> Any:
    """Create PUT endpoint handler for a model.

    Args:
        model: Model class
        databaseManager: DatabaseManager instance for database operations

    Returns:
        Async handler function
    """

    async def handler(request: Request) -> JSONResponse:
        """Handle PUT requests."""
        if databaseManager is None:
            return JSONResponse(
                {"error": "Database not configured"}, status_code=500
            )

        config = model.getConfiguration()
        if config.authentication_class:
            requiredRoles = config.required_roles.get("PUT", [])
            authMiddleware = AuthenticationMiddleware(config.authentication_class, requiredRoles)
            authResponse = await authMiddleware.process(request)
            if authResponse:
                return authResponse

        try:
            modelId = int(request.path_params.get("id", 0))
        except (ValueError, TypeError):
            return JSONResponse(
                {"error": "Invalid ID format"}, status_code=400
            )

        try:
            body = await request.json()
        except Exception as e:
            raise ValidationError(f"Invalid JSON in request body: {e}") from e

        try:
            async with databaseManager.sessionContext() as session:
                result = await session.execute(
                    select(model).where(model.id == modelId)
                )
                instance = result.scalar_one_or_none()

                if instance is None:
                    return JSONResponse(
                        {"error": f"{model.__name__} not found"},
                        status_code=404
                    )

                for key, value in body.items():
                    if hasattr(instance, key) and key != "id":
                        setattr(instance, key, value)

                await session.commit()
                await session.refresh(instance)

                serialized = serializeModel(instance)
                tableName = model.getTableName()

                config = model.getConfiguration()
                if config.caching_class:
                    cacheMiddleware = CacheMiddleware(config.caching_class)
                    await cacheMiddleware.invalidateCache(tableName, str(modelId))

                websocketManager = getWebSocketManager()
                await websocketManager.broadcast(tableName, "update", serialized)

                return JSONResponse(serialized, status_code=200)

        except ValidationError as e:
            return JSONResponse(
                {"error": "Validation failed", "detail": str(e)},
                status_code=400
            )
        except NoResultFound:
            return JSONResponse(
                {"error": f"{model.__name__} not found"},
                status_code=404
            )
        except IntegrityError as e:
            if 'session' in locals():
                await session.rollback()
            return JSONResponse(
                {"error": "Database constraint violation", "detail": str(e)},
                status_code=400
            )
        except OperationalError as e:
            if 'session' in locals():
                await session.rollback()
            return JSONResponse(
                {"error": "Database connection error", "detail": str(e)},
                status_code=500
            )
        except Exception as e:
            if 'session' in locals():
                await session.rollback()
            return JSONResponse(
                {"error": "Database operation failed", "detail": str(e)},
                status_code=500
            )

    return handler

