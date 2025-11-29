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

                # Exclude id and timestamp fields (same as POST handler)
                excluded_fields = {"id", "created_at", "updated_at"}
                requiredFields = [
                    col.name for col in inspector.columns
                    if not col.nullable 
                    and col.name not in excluded_fields
                    and col.default is None
                    and col.server_default is None
                ]

                # Validate required fields (but allow optional fields to be missing)
                missingFields = [field for field in requiredFields if field not in inputData]
                if missingFields:
                    # Return error but don't fail the mutation - let the database handle defaults
                    # Some fields like is_active might have defaults
                    # Only fail if truly required fields are missing
                    criticalFields = [f for f in missingFields if f not in ["is_active", "created_at", "updated_at"]]
                    if criticalFields:
                        return {"error": f"Missing required fields: {', '.join(criticalFields)}"}

                instanceData = {}
                for column in inspector.columns:
                    columnName = column.name
                    # Skip excluded fields (id and timestamp fields with server defaults)
                    if columnName in excluded_fields:
                        continue
                    if columnName in inputData:
                        instanceData[columnName] = inputData[columnName]
                    elif not column.nullable and column.default is None and column.server_default is None:
                        # Provide defaults for required fields without defaults
                        typeStr = str(column.type).lower()
                        if "bool" in typeStr or "boolean" in typeStr:
                            instanceData[columnName] = True  # Default boolean to True
                        elif "int" in typeStr or "integer" in typeStr:
                            instanceData[columnName] = 0  # Default integer to 0
                        elif "varchar" in typeStr or "text" in typeStr or "string" in typeStr:
                            instanceData[columnName] = ""  # Default string to empty

                # Use insert().values() to exclude columns with server defaults (same as POST handler)
                from sqlalchemy import insert
                insertData = {k: v for k, v in instanceData.items() if k not in excluded_fields}
                stmt = insert(model).values(**insertData).returning(model)
                result = await session.execute(stmt)
                instance = result.scalar_one()
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

