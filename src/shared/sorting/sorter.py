"""Sorting utilities."""

from typing import Any, Optional
from sqlalchemy import Column, desc


class Sorter:
    """Base class for sorting implementations."""

    @staticmethod
    def apply(query: Any, sortParam: Optional[str], model: Any) -> Any:
        """Apply sorting to a query.

        Args:
            query: SQLAlchemy select query
            sortParam: Sort parameter (e.g., "name", "-name" for descending, "name,price" for multiple)
            model: Model class for column lookup

        Returns:
            Sorted query
        """
        if not sortParam:
            return query

        orderByClauses = []

        for fieldSpec in sortParam.split(","):
            fieldSpec = fieldSpec.strip()
            if not fieldSpec:
                continue

            descending = fieldSpec.startswith("-")
            fieldName = fieldSpec.lstrip("-")

            if not hasattr(model, fieldName):
                continue

            column: Column = getattr(model, fieldName)

            if descending:
                orderByClauses.append(desc(column))
            else:
                orderByClauses.append(column)

        if orderByClauses:
            query = query.order_by(*orderByClauses)

        return query

