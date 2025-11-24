"""REST DELETE endpoint handler."""

from typing import Any, Optional, Type
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, OperationalError

from src.domain.entities.rest_endpoint import RestEndpoint
from src.infrastructure.database.connection import DatabaseManager
from src.presentation.middleware.auth import AuthenticationMiddleware
from src.presentation.middleware.cache import CacheMiddleware
from src.presentation.websocket.handler import getWebSocketManager


def deleteHandler(model: Type[RestEndpoint], databaseManager: Optional[DatabaseManager] = None) -> Any:
    """Create DELETE endpoint handler for a model.

    Args:
        model: Model class
        databaseManager: DatabaseManager instance for database operations

    Returns:
        Async handler function
    """

    async def handler(request: Request) -> Response:
        """Handle DELETE requests."""
        if databaseManager is None:
            return JSONResponse(
                {"error": "Database not configured"}, status_code=500
            )

        config = model.getConfiguration()
        if config.authentication_class:
            requiredRoles = config.required_roles.get("DELETE", [])
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

                tableName = model.getTableName()
                deletedData = {"id": instance.id}

                await session.delete(instance)
                await session.commit()

                config = model.getConfiguration()
                if config.caching_class:
                    cacheMiddleware = CacheMiddleware(config.caching_class)
                    await cacheMiddleware.invalidateCache(tableName, str(modelId))

                websocketManager = getWebSocketManager()
                await websocketManager.broadcast(tableName, "delete", deletedData)

                return Response(status_code=204)

        except NoResultFound:
            return JSONResponse(
                {"error": f"{model.__name__} not found"},
                status_code=404
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

