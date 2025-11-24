"""Base Paginator class."""

from typing import Any, Optional
from starlette.requests import Request


class Paginator:
    """Base class for pagination implementations."""

    def __init__(self, request: Request) -> None:
        """Initialize paginator.

        Args:
            request: Starlette request object
        """
        self.request = request

    def paginate(self, query: Any) -> Any:
        """Paginate a query.

        Args:
            query: SQLAlchemy query or similar

        Returns:
            Paginated result object with items, total, page, pages, etc.
        """
        raise NotImplementedError("Subclasses must implement paginate method")

