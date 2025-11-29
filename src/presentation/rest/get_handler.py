"""REST GET endpoint handler."""

from typing import Any, Optional, Type
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, OperationalError

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ValidationError, DatabaseError, NotFoundError, AuthenticationError, AuthorizationError
from src.infrastructure.database.connection import DatabaseManager
from src.presentation.middleware.auth import AuthenticationMiddleware
from src.presentation.middleware.cache import CacheMiddleware
from src.shared.filtering.filter import Filter
from src.shared.pagination.paginator import DefaultPaginator
from src.shared.serialization.serializer import serializeModel, serializeModelList
from src.shared.sorting.sorter import Sorter


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
) -> Optional[RestEndpoint]:
    """Get instance by ID from database."""
    result = await session.execute(
        select(model).where(model.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        raise NotFoundError(f"{model.__name__} not found")
    return instance


async def _handle_get_by_id(
    request: Request,
    model: Type[RestEndpoint],
    model_id: int,
    database_manager: DatabaseManager
) -> JSONResponse:
    """Handle GET by ID requests."""
    config = model.getConfiguration()
    table_name = model.getTableName()

    if config.caching_class:
        cache_middleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
        cached_response = await cache_middleware.getCachedResponse(request, table_name, str(model_id))
        if cached_response:
            return cached_response

    async with database_manager.sessionContext() as session:
        instance = await _get_instance_by_id(session, model, model_id)

    serialized = serializeModel(instance)
    response = JSONResponse(serialized, status_code=200)

    if config.caching_class:
        cache_middleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
        await cache_middleware.setCachedResponse(request, table_name, response, str(model_id))

    return response


async def _handle_get_list(
    request: Request,
    model: Type[RestEndpoint],
    database_manager: DatabaseManager
) -> JSONResponse:
    """Handle list requests with pagination, filtering, sorting."""
    config = model.getConfiguration()
    table_name = model.getTableName()

    if config.caching_class and "GET" in (config.caching_method_names or ["GET"]):
        cache_middleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
        cached_response = await cache_middleware.getCachedResponse(request, table_name)
        if cached_response:
            return cached_response

    async with database_manager.sessionContext() as session:
        query = select(model)

        filtering_enabled = getattr(model, "_filtering_enabled", True)
        if filtering_enabled:
            filter_params = {
                key: value
                for key, value in request.query_params.items()
                if "__" in key
            }
            if filter_params:
                query = Filter.apply(query, filter_params, model)

        sorting_enabled = getattr(model, "_sorting_enabled", True)
        if sorting_enabled:
            sort_param = request.query_params.get("sort")
            if sort_param:
                query = Sorter.apply(query, sort_param, model)

        paginator = DefaultPaginator(request)
        paginated_result = await paginator.paginate(query, session, model)

        serialized_items = serializeModelList(paginated_result["items"])

        response_data = {
            "items": serialized_items,
            "total": paginated_result["total"],
            "page": paginated_result["page"],
            "limit": paginated_result["limit"],
            "pages": paginated_result["pages"],
            "next_page": paginated_result["next_page"],
            "prev_page": paginated_result["prev_page"],
        }

        response = JSONResponse(response_data, status_code=200)

        if config.caching_class and "GET" in (config.caching_method_names or ["GET"]):
            cache_middleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
            await cache_middleware.setCachedResponse(request, table_name, response)

        return response


def getHandler(model: Type[RestEndpoint], databaseManager: Optional[DatabaseManager] = None) -> Any:
    """Create GET endpoint handler for a model.

    Args:
        model: Model class
        databaseManager: DatabaseManager instance for database operations

    Returns:
        Async handler function
    """

    async def handler(request: Request) -> JSONResponse:
        """Handle GET requests."""
        if databaseManager is None:
            raise DatabaseError("Database not configured")

        await _check_authentication(request, model, "GET")

        model_id = request.path_params.get("id")
        if model_id:
            model_id_int = _validate_id(model_id)
            return await _handle_get_by_id(request, model, model_id_int, databaseManager)

        return await _handle_get_list(request, model, databaseManager)

    return handler
