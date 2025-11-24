"""GraphQL query resolvers."""

from typing import Any, Dict, List, Optional, Type
from sqlalchemy import select, func

from src.domain.entities.rest_endpoint import RestEndpoint
from src.infrastructure.database.connection import DatabaseManager
from src.shared.serialization.serializer import serializeModel, serializeModelList


async def resolveQuery(
    queryName: str,
    model: Type[RestEndpoint],
    databaseManager: Optional[DatabaseManager],
    **kwargs: Any
) -> Any:
    """Resolve a GraphQL query.

    Args:
        queryName: Name of the query
        model: Model class for the query
        databaseManager: DatabaseManager instance
        **kwargs: Query arguments (e.g., id, filters, pagination)

    Returns:
        Query result
    """
    if databaseManager is None:
        return {"error": "Database not configured"}

    try:
        async with databaseManager.sessionContext() as session:
            if queryName.endswith("s") or queryName == "list":
                tableName = model.getTableName()
                if queryName.startswith(tableName) or queryName == "list":
                    query = select(model)

                    if "filters" in kwargs:
                        from src.shared.filtering.filter import Filter
                        query = Filter.apply(query, kwargs["filters"], model)

                    if "sort" in kwargs:
                        from src.shared.sorting.sorter import Sorter
                        query = Sorter.apply(query, kwargs.get("sort"), model)

                    if "page" in kwargs or "limit" in kwargs:
                        from src.shared.pagination.paginator import DefaultPaginator
                        from starlette.requests import Request
                        request = kwargs.get("request")
                        if request:
                            paginator = DefaultPaginator(request)
                            paginatedResult = await paginator.paginate(query, session, model)
                            return {
                                "items": serializeModelList(paginatedResult["items"]),
                                "total": paginatedResult["total"],
                                "page": paginatedResult["page"],
                                "limit": paginatedResult["limit"],
                            }

                    result = await session.execute(query)
                    instances = result.scalars().all()
                    return serializeModelList(instances)

            elif "id" in kwargs:
                modelId = kwargs["id"]
                result = await session.execute(
                    select(model).where(model.id == modelId)
                )
                instance = result.scalar_one_or_none()

                if instance is None:
                    return {"error": f"{model.__name__} not found"}

                return serializeModel(instance)

            return {"error": f"Unknown query: {queryName}"}

    except Exception as e:
        return {"error": f"Database operation failed: {str(e)}"}

