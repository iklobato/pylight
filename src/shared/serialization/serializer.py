"""Model serialization utilities."""

from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy import inspect


def serializeModel(instance: Any, includeRelationships: bool = False) -> Dict[str, Any]:
    """Serialize a SQLAlchemy model instance to a dictionary.

    Args:
        instance: SQLAlchemy model instance
        includeRelationships: Whether to include relationship data (default: False, only IDs)

    Returns:
        Dictionary representation of the model
    """
    if instance is None:
        return None

    inspector = inspect(instance.__class__)
    result: Dict[str, Any] = {}

    for column in inspector.columns:
        columnName = column.name
        value = getattr(instance, columnName, None)

        if isinstance(value, datetime):
            result[columnName] = value.isoformat()
        elif value is None:
            result[columnName] = None
        else:
            result[columnName] = value

    if includeRelationships:
        for relationship in inspector.relationships:
            relationshipName = relationship.key
            relationshipValue = getattr(instance, relationshipName, None)

            if relationshipValue is None:
                result[relationshipName] = None
            elif hasattr(relationshipValue, "__iter__") and not isinstance(relationshipValue, str):
                result[relationshipName] = [
                    serializeModel(item, includeRelationships=False) for item in relationshipValue
                ]
            else:
                result[relationshipName] = serializeModel(relationshipValue, includeRelationships=False)
    else:
        for relationship in inspector.relationships:
            relationshipName = relationship.key
            relationshipValue = getattr(instance, relationshipName, None)

            if relationshipValue is None:
                result[relationshipName] = None
            elif hasattr(relationshipValue, "__iter__") and not isinstance(relationshipValue, str):
                foreignKeyColumn = list(relationship.local_columns)[0]
                result[relationshipName] = [getattr(item, foreignKeyColumn.name) for item in relationshipValue]
            else:
                foreignKeyColumn = list(relationship.local_columns)[0]
                result[relationshipName] = getattr(relationshipValue, foreignKeyColumn.name)

    return result


def serializeModelList(instances: list[Any], includeRelationships: bool = False) -> list[Dict[str, Any]]:
    """Serialize a list of SQLAlchemy model instances.

    Args:
        instances: List of SQLAlchemy model instances
        includeRelationships: Whether to include relationship data

    Returns:
        List of dictionary representations
    """
    return [serializeModel(instance, includeRelationships) for instance in instances]

