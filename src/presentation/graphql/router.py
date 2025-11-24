"""GraphQL router integration with Starlette."""

from typing import Any, Optional
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.infrastructure.database.connection import DatabaseManager
from src.presentation.graphql.queries import resolveQuery
from src.presentation.graphql.mutations import resolveMutation


def createGraphQLRoute(databaseManager: Optional[DatabaseManager] = None, models: list = None) -> Route:
    """Create GraphQL route for Starlette.

    Args:
        databaseManager: DatabaseManager instance
        models: List of registered models

    Returns:
        Starlette Route for GraphQL endpoint
    """
    async def graphqlHandler(request: Request) -> JSONResponse:
        """Handle GraphQL requests."""
        if request.method == "GET":
            return JSONResponse({"message": "GraphQL endpoint - use POST for queries"})

        try:
            body = await request.json()
            query = body.get("query", "")
            variables = body.get("variables", {})

            operationName = body.get("operationName", "")

            if not query:
                return JSONResponse({"error": "Query is required"}, status_code=400)

            if "query" in query.lower():
                queryName = operationName or query.split("{")[0].strip().replace("query", "").strip()
                model = None
                if models:
                    for m in models:
                        if queryName.lower().startswith(m.getTableName().lower()):
                            model = m
                            break

                if model:
                    result = await resolveQuery(
                        queryName,
                        model,
                        databaseManager,
                        request=request,
                        **variables
                    )
                    return JSONResponse({"data": result})
                else:
                    return JSONResponse({"error": "Model not found for query"}, status_code=400)

            elif "mutation" in query.lower():
                mutationName = operationName or query.split("{")[0].strip().replace("mutation", "").strip()
                model = None
                if models:
                    for m in models:
                        if mutationName.lower().startswith(m.getTableName().lower()):
                            model = m
                            break

                if model:
                    result = await resolveMutation(
                        mutationName,
                        model,
                        databaseManager,
                        **variables
                    )
                    return JSONResponse({"data": result})
                else:
                    return JSONResponse({"error": "Model not found for mutation"}, status_code=400)

            return JSONResponse({"error": "Invalid GraphQL query"}, status_code=400)

        except Exception as e:
            return JSONResponse(
                {"error": f"GraphQL operation failed: {str(e)}"},
                status_code=500
            )

    return Route("/graphql", graphqlHandler, methods=["GET", "POST"])

