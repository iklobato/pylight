"""Default pagination implementation."""

from typing import Any, Dict
from starlette.requests import Request
from sqlalchemy import func, select

from src.shared.pagination.base import Paginator


class DefaultPaginator(Paginator):
    """Default pagination implementation."""

    async def paginate(self, query: Any, session: Any, model: Any) -> Dict[str, Any]:
        """Paginate a query with page and limit parameters.

        Args:
            query: SQLAlchemy select query
            session: Database session for executing queries
            model: Model class for count query

        Returns:
            Dictionary with paginated results and metadata
        """
        try:
            page = int(self.request.query_params.get("page", 1))
        except (ValueError, TypeError):
            page = 1

        try:
            limit = int(self.request.query_params.get("limit", 10))
        except (ValueError, TypeError):
            limit = 10

        if limit > 100:
            limit = 100

        if page < 1:
            page = 1

        if limit < 1:
            limit = 10

        offset = (page - 1) * limit

        countQuery = select(func.count()).select_from(model)
        countResult = await session.execute(countQuery)
        total = countResult.scalar() or 0

        paginatedQuery = query.offset(offset).limit(limit)
        result = await session.execute(paginatedQuery)
        items = result.scalars().all()

        totalPages = (total + limit - 1) // limit if limit > 0 else 0
        nextPage = page + 1 if (page * limit) < total else None
        prevPage = page - 1 if page > 1 else None

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": totalPages,
            "next_page": nextPage,
            "prev_page": prevPage,
        }

