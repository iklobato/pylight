"""Filtering utilities."""

from typing import Any, Dict
from sqlalchemy import Column, and_, inspect


class Filter:
    """Base class for filtering implementations."""

    @staticmethod
    def _convertValue(value: Any, column: Column) -> Any:
        """Convert filter value to appropriate type based on column type.

        Args:
            value: Filter value (usually a string from query params)
            column: SQLAlchemy Column object

        Returns:
            Converted value with appropriate type
        """
        # If value is already the correct type, return as-is
        if value is None:
            return None

        typeStr = str(column.type).lower()

        # Integer types
        if "int" in typeStr or "integer" in typeStr:
            if isinstance(value, int):
                return value
            try:
                return int(value)
            except (ValueError, TypeError):
                return value  # Return as-is if conversion fails

        # Numeric/Decimal types
        elif "numeric" in typeStr or "decimal" in typeStr or "float" in typeStr:
            if isinstance(value, (int, float)):
                return value
            try:
                return float(value)
            except (ValueError, TypeError):
                return value  # Return as-is if conversion fails

        # Boolean types
        elif "bool" in typeStr or "boolean" in typeStr:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ('true', '1', 'yes', 'on'):
                    return True
                elif value.lower() in ('false', '0', 'no', 'off'):
                    return False
            return value  # Return as-is if conversion fails

        # String types - keep as string
        # JSON types - keep as-is (will be handled by SQLAlchemy)
        # DateTime types - keep as string (SQLAlchemy will parse)
        return value

    @staticmethod
    def apply(query: Any, filterParams: Dict[str, Any], model: Any) -> Any:
        """Apply filters to a query.

        Args:
            query: SQLAlchemy select query
            filterParams: Dictionary of filter parameters (e.g., {"name__eq": "test", "price__gte": "100"})
            model: Model class for column lookup

        Returns:
            Filtered query
        """
        if not filterParams:
            return query

        conditions = []
        inspector = inspect(model)

        for key, value in filterParams.items():
            if "__" not in key:
                continue

            fieldName, operator = key.rsplit("__", 1)

            if not hasattr(model, fieldName):
                continue

            column: Column = getattr(model, fieldName)

            # Convert value to appropriate type
            convertedValue = Filter._convertValue(value, column)

            if operator == "eq":
                conditions.append(column == convertedValue)
            elif operator == "ne":
                conditions.append(column != convertedValue)
            elif operator == "gt":
                conditions.append(column > convertedValue)
            elif operator == "gte":
                conditions.append(column >= convertedValue)
            elif operator == "lt":
                conditions.append(column < convertedValue)
            elif operator == "lte":
                conditions.append(column <= convertedValue)
            elif operator == "like":
                # Like operator works with strings, no conversion needed
                conditions.append(column.like(f"%{value}%"))
            elif operator == "in":
                # For "in" operator, convert each value in the list
                if isinstance(value, list):
                    convertedList = [Filter._convertValue(v, column) for v in value]
                    conditions.append(column.in_(convertedList))
                else:
                    # Split comma-separated string and convert each
                    values = [Filter._convertValue(v.strip(), column) for v in value.split(",") if v.strip()]
                    conditions.append(column.in_(values))

        if conditions:
            query = query.where(and_(*conditions))

        return query

