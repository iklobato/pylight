"""REST PUT endpoint handler."""

from typing import Any, Optional, Type, Dict, Callable
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import select, inspect
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ValidationError, DatabaseError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.database.connection import DatabaseManager
from src.presentation.middleware.auth import AuthenticationMiddleware
from src.presentation.middleware.cache import CacheMiddleware
from src.presentation.websocket.handler import getWebSocketManager
from src.shared.serialization.serializer import serializeModel


def _convert_to_int(value: Any, column_type: str, column_name: str) -> int:
    """Convert value to integer."""
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValidationError(field_errors=[{
            "field": column_name,
            "message": f"Field '{column_name}' must be an integer, got {type(value).__name__}"
        }])


def _convert_to_float(value: Any, column_type: str, column_name: str) -> float:
    """Convert value to float."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValidationError(field_errors=[{
            "field": column_name,
            "message": f"Field '{column_name}' must be a number, got {type(value).__name__}"
        }])


def _convert_to_bool(value: Any, column_type: str, column_name: str) -> bool:
    """Convert value to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        if value.lower() in ('false', '0', 'no', 'off'):
            return False
    raise ValidationError(field_errors=[{
        "field": column_name,
        "message": f"Field '{column_name}' must be a boolean, got {type(value).__name__}"
    }])


def _convert_to_str(value: Any, column_type: str, column_name: str) -> str:
    """Convert value to string."""
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except (ValueError, TypeError):
        raise ValidationError(field_errors=[{
            "field": column_name,
            "message": f"Field '{column_name}' must be a string, got {type(value).__name__}"
        }])


def _convert_to_json(value: Any, column_type: str, column_name: str) -> Dict | list:
    """Convert and validate JSON value."""
    if isinstance(value, (dict, list)):
        return value
    raise ValidationError(field_errors=[{
        "field": column_name,
        "message": f"Field '{column_name}' must be a JSON object or array, got {type(value).__name__}"
    }])


# Type conversion strategy pattern registry
_TYPE_CONVERTERS: Dict[str, Callable[[Any, str, str], Any]] = {
    "int": _convert_to_int,
    "integer": _convert_to_int,
    "float": _convert_to_float,
    "numeric": _convert_to_float,
    "decimal": _convert_to_float,
    "bool": _convert_to_bool,
    "boolean": _convert_to_bool,
    "varchar": _convert_to_str,
    "text": _convert_to_str,
    "string": _convert_to_str,
    "char": _convert_to_str,
    "json": _convert_to_json,
    "jsonb": _convert_to_json,
}


def _convert_field_value(value: Any, column_type: str, column_name: str) -> Any:
    """Convert field value using strategy pattern."""
    type_str = str(column_type).lower()
    for key, converter in _TYPE_CONVERTERS.items():
        if key in type_str:
            return converter(value, column_type, column_name)
    return value


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


async def _validate_and_convert_types(
    body: Dict[str, Any],
    model: Type[RestEndpoint],
    instance: RestEndpoint
) -> Dict[str, Any]:
    """Validate and convert field types using strategy pattern."""
    inspector = inspect(model)
    excluded_fields = {"id", "created_at", "updated_at"}
    update_data = {}

    column_map = {col.name: col for col in inspector.columns}

    for key, value in body.items():
        if key in excluded_fields:
            continue
        if not hasattr(instance, key):
            continue

        column = column_map.get(key)
        if not column:
            continue

        column_type = column.type
        try:
            converted_value = _convert_field_value(value, column_type, key)
            update_data[key] = converted_value
        except ValidationError:
            raise

    return update_data


async def _update_instance(
    session: Any,
    instance: RestEndpoint,
    update_data: Dict[str, Any]
) -> RestEndpoint:
    """Update instance in database."""
    for key, value in update_data.items():
        setattr(instance, key, value)

    await session.commit()
    await session.refresh(instance)
    return instance


async def _handle_side_effects(
    model: Type[RestEndpoint],
    instance: RestEndpoint,
    operation: str,
    request: Request
) -> None:
    """Handle cache invalidation and WebSocket broadcasting."""
    table_name = model.getTableName()
    serialized = serializeModel(instance)

    config = model.getConfiguration()
    if config.caching_class:
        cache_middleware = CacheMiddleware(config.caching_class)
        await cache_middleware.invalidateCache(table_name, str(instance.id))

    websocket_manager = getWebSocketManager()
    await websocket_manager.broadcast(table_name, operation, serialized)


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
            raise DatabaseError("Database not configured")

        await _check_authentication(request, model, "PUT")

        model_id = _validate_id(request.path_params.get("id", "0"))

        try:
            body = await request.json()
        except Exception as e:
            raise ValidationError(f"Invalid JSON in request body: {e}") from e

        async with databaseManager.sessionContext() as session:
            instance = await _get_instance_by_id(session, model, model_id)
            update_data = await _validate_and_convert_types(body, model, instance)
            await _update_instance(session, instance, update_data)

        await _handle_side_effects(model, instance, "update", request)

        serialized = serializeModel(instance)
        return JSONResponse(serialized, status_code=200)

    return handler
