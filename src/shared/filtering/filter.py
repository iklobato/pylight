"""Filtering utilities."""

from typing import Any, Dict
from sqlalchemy import Column, and_


class Filter:
    """Base class for filtering implementations."""

    @staticmethod
    def apply(query: Any, filterParams: Dict[str, Any], model: Any) -> Any:
        """Apply filters to a query.

        Args:
            query: SQLAlchemy select query
            filterParams: Dictionary of filter parameters (e.g., {"name__eq": "test", "price__gte": 100})
            model: Model class for column lookup

        Returns:
            Filtered query
        """
        if not filterParams:
            return query

        conditions = []

        for key, value in filterParams.items():
            if "__" not in key:
                continue

            fieldName, operator = key.rsplit("__", 1)

            if not hasattr(model, fieldName):
                continue

            column: Column = getattr(model, fieldName)

            if operator == "eq":
                conditions.append(column == value)
            elif operator == "ne":
                conditions.append(column != value)
            elif operator == "gt":
                conditions.append(column > value)
            elif operator == "gte":
                conditions.append(column >= value)
            elif operator == "lt":
                conditions.append(column < value)
            elif operator == "lte":
                conditions.append(column <= value)
            elif operator == "like":
                conditions.append(column.like(f"%{value}%"))
            elif operator == "in":
                if isinstance(value, list):
                    conditions.append(column.in_(value))
                else:
                    conditions.append(column.in_(value.split(",")))

        if conditions:
            query = query.where(and_(*conditions))

        return query

