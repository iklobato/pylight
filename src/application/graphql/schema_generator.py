"""GraphQL schema generator."""

from typing import Any, Type

from src.domain.entities.rest_endpoint import RestEndpoint


class GraphQLSchemaGenerator:
    """Generates GraphQL schema from RestEndpoint models."""

    @staticmethod
    def generateSchema(models: list[Type[RestEndpoint]]) -> dict[str, Any]:
        """Generate GraphQL schema for models.

        Args:
            models: List of model classes

        Returns:
            GraphQL schema dictionary
        """
        return {"types": [model.__name__ for model in models], "queries": [], "mutations": []}

