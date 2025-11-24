"""REST endpoint generator."""

from typing import Any, Type
from starlette.routing import Route

from typing import Any, Type
from starlette.routing import Route

from src.domain.entities.rest_endpoint import RestEndpoint
from src.presentation.rest.get_handler import getHandler
from src.presentation.rest.post_handler import postHandler
from src.presentation.rest.put_handler import putHandler
from src.presentation.rest.delete_handler import deleteHandler


class RESTGenerator:
    """Generates REST endpoints from RestEndpoint models."""

    @staticmethod
    def generateRoutes(
        model: Type[RestEndpoint], databaseManager: Any = None, basePath: str = "/api"
    ) -> list[Route]:
        """Generate REST routes for a model.

        Args:
            model: Model class inheriting from RestEndpoint
            databaseManager: DatabaseManager instance for database operations
            basePath: Base path for API endpoints

        Returns:
            List of Starlette Route objects
        """
        tableName = model.getTableName()
        routes: list[Route] = []

        routes.append(
            Route(
                f"{basePath}/{tableName}",
                getHandler(model, databaseManager),
                methods=["GET"],
                name=f"list_{tableName}",
            )
        )

        routes.append(
            Route(
                f"{basePath}/{tableName}",
                postHandler(model, databaseManager),
                methods=["POST"],
                name=f"create_{tableName}",
            )
        )

        routes.append(
            Route(
                f"{basePath}/{tableName}/{{id}}",
                getHandler(model, databaseManager),
                methods=["GET"],
                name=f"get_{tableName}",
            )
        )

        routes.append(
            Route(
                f"{basePath}/{tableName}/{{id}}",
                putHandler(model, databaseManager),
                methods=["PUT"],
                name=f"update_{tableName}",
            )
        )

        routes.append(
            Route(
                f"{basePath}/{tableName}/{{id}}",
                deleteHandler(model, databaseManager),
                methods=["DELETE"],
                name=f"delete_{tableName}",
            )
        )

        return routes

