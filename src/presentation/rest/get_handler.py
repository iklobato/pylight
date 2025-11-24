"""REST GET endpoint handler."""

from typing import Any, Optional, Type
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, OperationalError

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ValidationError, DatabaseError, NotFoundError, AuthenticationError
from src.infrastructure.database.connection import DatabaseManager
from src.presentation.middleware.auth import AuthenticationMiddleware
from src.presentation.middleware.cache import CacheMiddleware
from src.shared.filtering.filter import Filter
from src.shared.pagination.paginator import DefaultPaginator
from src.shared.serialization.serializer import serializeModel, serializeModelList
from src.shared.sorting.sorter import Sorter


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
            return JSONResponse(
                {"error": "Database not configured"}, status_code=500
            )

        config = model.getConfiguration()
        if config.authentication_class:
            requiredRoles = config.required_roles.get("GET", [])
            authMiddleware = AuthenticationMiddleware(config.authentication_class, requiredRoles)
            authResponse = await authMiddleware.process(request)
            if authResponse:
                return authResponse

        modelId = request.path_params.get("id")

        if modelId:
            try:
                modelIdInt = int(modelId)
            except ValueError:
                return JSONResponse(
                    {"error": "Invalid ID format"}, status_code=400
                )
            return await getByIdHandler(request, model, modelIdInt, databaseManager)
        else:
            return await listHandler(request, model, databaseManager)

    return handler


async def getByIdHandler(
    request: Request,
    model: Type[RestEndpoint],
    modelId: int,
    databaseManager: DatabaseManager
) -> JSONResponse:
    """Handle GET by ID requests."""
    config = model.getConfiguration()
    tableName = model.getTableName()

    if config.caching_class:
        cacheMiddleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
        cachedResponse = await cacheMiddleware.getCachedResponse(request, tableName, str(modelId))
        if cachedResponse:
            return cachedResponse

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

            serialized = serializeModel(instance)
            response = JSONResponse(serialized, status_code=200)

            if config.caching_class:
                cacheMiddleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
                await cacheMiddleware.setCachedResponse(request, tableName, response, str(modelId))

            return response

    except Exception as e:
        return JSONResponse(
            {"error": "Database operation failed", "detail": str(e)},
            status_code=500
        )


async def listHandler(
    request: Request,
    model: Type[RestEndpoint],
    databaseManager: DatabaseManager
) -> JSONResponse:
    """Handle list requests with pagination, filtering, sorting."""
    config = model.getConfiguration()
    tableName = model.getTableName()

    if config.caching_class and "GET" in (config.caching_method_names or ["GET"]):
        cacheMiddleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
        cachedResponse = await cacheMiddleware.getCachedResponse(request, tableName)
        if cachedResponse:
            return cachedResponse

    try:
        async with databaseManager.sessionContext() as session:
            query = select(model)

            filteringEnabled = getattr(model, "_filtering_enabled", True)
            if filteringEnabled:
                filterParams = {
                    key: value
                    for key, value in request.query_params.items()
                    if "__" in key
                }
                if filterParams:
                    query = Filter.apply(query, filterParams, model)

            sortingEnabled = getattr(model, "_sorting_enabled", True)
            if sortingEnabled:
                sortParam = request.query_params.get("sort")
                if sortParam:
                    query = Sorter.apply(query, sortParam, model)

            paginator = DefaultPaginator(request)
            paginatedResult = await paginator.paginate(query, session, model)

            serializedItems = serializeModelList(paginatedResult["items"])

            responseData = {
                "items": serializedItems,
                "total": paginatedResult["total"],
                "page": paginatedResult["page"],
                "limit": paginatedResult["limit"],
                "pages": paginatedResult["pages"],
                "next_page": paginatedResult["next_page"],
                "prev_page": paginatedResult["prev_page"],
            }

            response = JSONResponse(responseData, status_code=200)

            if config.caching_class and "GET" in (config.caching_method_names or ["GET"]):
                cacheMiddleware = CacheMiddleware(config.caching_class, config.caching_method_names or ["GET"])
                await cacheMiddleware.setCachedResponse(request, tableName, response)

            return response

    except Exception as e:
        return JSONResponse(
            {"error": "Database operation failed", "detail": str(e)},
            status_code=500
        )

