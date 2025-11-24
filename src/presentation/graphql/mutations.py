"""GraphQL mutation resolvers."""

from typing import Any, Dict, Optional, Type
from sqlalchemy import select, inspect
from sqlalchemy.exc import IntegrityError

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ValidationError
from src.infrastructure.database.connection import DatabaseManager
from src.shared.serialization.serializer import serializeModel


async def resolveMutation(
    mutationName: str,
    model: Type[RestEndpoint],
    databaseManager: Optional[DatabaseManager],
    **kwargs: Any
) -> Any:
    """Resolve a GraphQL mutation.

    Args:
        mutationName: Name of the mutation (create, update, delete)
        model: Model class for the mutation
        databaseManager: DatabaseManager instance
        **kwargs: Mutation arguments (input data, id)

    Returns:
        Mutation result
    """
    if databaseManager is None:
        return {"error": "Database not configured"}

    try:
        async with databaseManager.sessionContext() as session:
            if mutationName.startswith("create"):
                inputData = kwargs.get("input", {})
                inspector = inspect(model)

                instanceData = {}
                for column in inspector.columns:
                    columnName = column.name
                    if columnName in inputData:
                        instanceData[columnName] = inputData[columnName]

                instance = model(**instanceData)
                session.add(instance)
                await session.commit()
                await session.refresh(instance)

                return serializeModel(instance)

            elif mutationName.startswith("update"):
                modelId = kwargs.get("id")
                inputData = kwargs.get("input", {})

                if not modelId:
                    return {"error": "ID is required for update"}

                result = await session.execute(
                    select(model).where(model.id == modelId)
                )
                instance = result.scalar_one_or_none()

                if instance is None:
                    return {"error": f"{model.__name__} not found"}

                for key, value in inputData.items():
                    if hasattr(instance, key) and key != "id":
                        setattr(instance, key, value)

                await session.commit()
                await session.refresh(instance)

                return serializeModel(instance)

            elif mutationName.startswith("delete"):
                modelId = kwargs.get("id")

                if not modelId:
                    return {"error": "ID is required for delete"}

                result = await session.execute(
                    select(model).where(model.id == modelId)
                )
                instance = result.scalar_one_or_none()

                if instance is None:
                    return {"error": f"{model.__name__} not found"}

                await session.delete(instance)
                await session.commit()

                return {"success": True, "id": modelId}

            return {"error": f"Unknown mutation: {mutationName}"}

    except IntegrityError as e:
        if 'session' in locals():
            await session.rollback()
        return {"error": f"Database constraint violation: {str(e)}"}
    except Exception as e:
        if 'session' in locals():
            await session.rollback()
        return {"error": f"Database operation failed: {str(e)}"}

