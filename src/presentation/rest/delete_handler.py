"""REST DELETE endpoint handler."""

from typing import Any, Optional, Type
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, OperationalError, IntegrityError

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ValidationError, DatabaseError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.database.connection import DatabaseManager
from src.presentation.middleware.auth import AuthenticationMiddleware
from src.presentation.middleware.cache import CacheMiddleware
from src.presentation.websocket.handler import getWebSocketManager


def _validate_id(id_str: str) -> int:
    """Validate and convert ID string to integer."""
    try:
        return int(id_str)
    except (ValueError, TypeError):
        raise ValidationError("Invalid ID format")


async def _check_authentication(
    request: Request,
    model: Type[RestEndpoint],
    method: str
) -> None:
    """Check authentication and raise if unauthorized."""
    config = model.getConfiguration()
    if not config.authentication_class:
        return

    required_roles = config.required_roles.get(method, [])
    auth_middleware = AuthenticationMiddleware(config.authentication_class, required_roles)
    auth_response = await auth_middleware.process(request)
    if auth_response:
        status_code = auth_response.status_code
        if status_code == 401:
            raise AuthenticationError("Authentication required")
        if status_code == 403:
            raise AuthorizationError("Authorization failed")
        raise AuthenticationError("Authentication failed")


async def _get_instance_by_id(
    session: Any,
    model: Type[RestEndpoint],
    instance_id: int
) -> RestEndpoint:
    """Get instance by ID from database."""
    result = await session.execute(
        select(model).where(model.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        raise NotFoundError(f"{model.__name__} not found")
    return instance


async def _delete_instance(
    session: Any,
    instance: RestEndpoint
) -> None:
    """Delete instance from database."""
    await session.delete(instance)
    await session.commit()


async def _handle_side_effects(
    model: Type[RestEndpoint],
    instance_id: int,
    operation: str
) -> None:
    """Handle cache invalidation and WebSocket broadcasting."""
    table_name = model.getTableName()
    deleted_data = {"id": instance_id}

    config = model.getConfiguration()
    if config.caching_class:
        cache_middleware = CacheMiddleware(config.caching_class)
        await cache_middleware.invalidateCache(table_name, str(instance_id))

    websocket_manager = getWebSocketManager()
    await websocket_manager.broadcast(table_name, operation, deleted_data)


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
            raise DatabaseError("Database not configured")

        await _check_authentication(request, model, "DELETE")

        model_id = _validate_id(request.path_params.get("id", "0"))

        async with databaseManager.sessionContext() as session:
            instance = await _get_instance_by_id(session, model, model_id)
            await _delete_instance(session, instance)

        await _handle_side_effects(model, instance.id, "delete")

        return Response(status_code=204)

    return handler
