"""REST POST endpoint handler."""

from typing import Any, Optional, Type
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, OperationalError

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ValidationError, DatabaseError
from src.infrastructure.database.connection import DatabaseManager
from src.presentation.middleware.auth import AuthenticationMiddleware
from src.presentation.middleware.cache import CacheMiddleware
from src.presentation.websocket.handler import getWebSocketManager
from src.shared.serialization.serializer import serializeModel


def postHandler(model: Type[RestEndpoint], databaseManager: Optional[DatabaseManager] = None) -> Any:
    """Create POST endpoint handler for a model.

    Args:
        model: Model class
        databaseManager: DatabaseManager instance for database operations

    Returns:
        Async handler function
    """

    async def handler(request: Request) -> JSONResponse:
        """Handle POST requests."""
        if databaseManager is None:
            return JSONResponse(
                {"error": "Database not configured"}, status_code=500
            )

        config = model.getConfiguration()
        if config.authentication_class:
            requiredRoles = config.required_roles.get("POST", [])
            authMiddleware = AuthenticationMiddleware(config.authentication_class, requiredRoles)
            authResponse = await authMiddleware.process(request)
            if authResponse:
                return authResponse

        try:
            body = await request.json()
        except Exception as e:
            raise ValidationError(f"Invalid JSON in request body: {e}") from e

        try:
            inspector = inspect(model)
            requiredFields = [
                col.name for col in inspector.columns
                if not col.nullable and col.name != "id" and col.default is None
            ]

            for field in requiredFields:
                if field not in body:
                    raise ValidationError(f"Missing required field: {field}")

            instanceData = {}
            for column in inspector.columns:
                columnName = column.name
                if columnName in body:
                    instanceData[columnName] = body[columnName]

            instance = model(**instanceData)

            async with databaseManager.sessionContext() as session:
                session.add(instance)
                await session.commit()
                await session.refresh(instance)

                serialized = serializeModel(instance)
                tableName = model.getTableName()
                location = f"{request.url.scheme}://{request.url.netloc}/api/{tableName}/{serialized.get('id')}"

                config = model.getConfiguration()
                if config.caching_class:
                    cacheMiddleware = CacheMiddleware(config.caching_class)
                    await cacheMiddleware.invalidateCache(tableName)

                websocketManager = getWebSocketManager()
                await websocketManager.broadcast(tableName, "create", serialized)

                return JSONResponse(
                    serialized,
                    status_code=201,
                    headers={"Location": location}
                )

        except ValidationError as e:
            return JSONResponse(
                {"error": "Validation failed", "detail": str(e)},
                status_code=400
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

