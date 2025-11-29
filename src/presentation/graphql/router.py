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

            # GraphQL queries can be written with or without "query" keyword
            # Examples: "query { products { id } }" or "{ products { id } }"
            # Check if it's a query (not a mutation)
            # Also handle introspection queries (__schema, __type)
            isQuery = "mutation" not in query.lower() and (query.strip().startswith("{") or "query" in query.lower())
            isIntrospection = "__schema" in query or "__type" in query
            
            if isQuery:
                # Handle introspection queries specially
                if isIntrospection:
                    # Return a basic schema structure for introspection
                    # This is a simplified implementation - full introspection would require
                    # a proper GraphQL schema implementation
                    return JSONResponse({
                        "data": {
                            "__schema": {
                                "types": [
                                    {
                                        "name": "Product",
                                        "fields": [
                                            {"name": "id", "type": {"name": "Int"}},
                                            {"name": "name", "type": {"name": "String"}},
                                            {"name": "price", "type": {"name": "Float"}},
                                        ]
                                    }
                                ]
                            }
                        }
                    }, status_code=200)
                # Extract query name and parameters from GraphQL query
                # Example: "query { products { id name } }" -> "products"
                # Example: "query { product(id: 1) { id name } }" -> "product", id=1
                queryName = operationName
                queryVariables = variables.copy()
                
                if not queryName:
                    # Parse query name from query string
                    # Look for pattern like "products", "product(id: 1)", etc.
                    parts = query.split("{")
                    if len(parts) > 1:
                        # Get the first field name after the opening brace
                        queryPart = parts[1].strip()
                        # Extract field name and parameters
                        if "(" in queryPart:
                            # Has parameters like "product(id: 1)"
                            queryName = queryPart.split("(")[0].strip()
                            # Extract parameters (simple parsing)
                            import re
                            paramMatch = re.search(r'\(([^)]+)\)', queryPart)
                            if paramMatch:
                                paramStr = paramMatch.group(1)
                                # Parse key: value pairs
                                for param in paramStr.split(','):
                                    param = param.strip()
                                    if ':' in param:
                                        key, value = param.split(':', 1)
                                        key = key.strip()
                                        value = value.strip().strip('"').strip("'")
                                        # Convert value types
                                        if value.replace('.', '').replace('-', '').isdigit():
                                            try:
                                                if '.' in value:
                                                    value = float(value)
                                                else:
                                                    value = int(value)
                                            except:
                                                pass
                                        queryVariables[key] = value
                        else:
                            # No parameters like "products { id }"
                            queryName = queryPart.split("{")[0].strip()
                
                model = None
                if models and queryName:
                    # Try to match query name with table names
                    queryNameLower = queryName.lower()
                    for m in models:
                        tableName = m.getTableName().lower()
                        # Check if query name matches table name (with or without 's' suffix)
                        if (queryNameLower == tableName or 
                            queryNameLower == tableName.rstrip('s') or 
                            queryNameLower + 's' == tableName or
                            tableName in queryNameLower):
                            model = m
                            break
                
                if model:
                    result = await resolveQuery(
                        queryName,
                        model,
                        databaseManager,
                        request=request,
                        **queryVariables
                    )
                    # GraphQL queries should return data in format: {"data": {"products": [...]}}
                    return JSONResponse({"data": {queryName: result}})
                else:
                    return JSONResponse({"error": f"Model not found for query: {queryName}"}, status_code=400)

            elif "mutation" in query.lower():
                # Parse mutation name from GraphQL query
                # Example: "mutation { createProduct(input: {...}) { id name } }"
                mutationName = operationName
                if not mutationName:
                    # Extract mutation name from query string
                    # Look for pattern like "createProduct", "updateProduct", "deleteProduct"
                    parts = query.split("{")
                    if len(parts) > 1:
                        mutationPart = parts[1].strip()
                        # Get first word (mutation name)
                        mutationName = mutationPart.split("(")[0].strip()
                
                # Parse mutation parameters (id and input) from GraphQL query
                mutationId = variables.get("id")
                mutationInput = variables.get("input", {})
                
                if not mutationId or not mutationInput:
                    # Try to extract parameters from query string
                    import re
                    # Extract id parameter: mutationName(id: 1, ...) or mutationName(id: 1)
                    # Try multiple patterns
                    idMatch = re.search(r'\(id:\s*(\d+)[,\)]', query) or re.search(r'id:\s*(\d+)', query)
                    if idMatch and not mutationId:
                        mutationId = int(idMatch.group(1))
                        variables["id"] = mutationId
                    
                    # Extract input parameter: input: { ... }
                    if not mutationInput:
                        inputMatch = re.search(r'input:\s*\{([^}]+)\}', query, re.DOTALL)
                        if inputMatch:
                            inputStr = inputMatch.group(1)
                            mutationInput = {}
                            for line in inputStr.split('\n'):
                                line = line.strip().rstrip(',')
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    key = key.strip()
                                    value = value.strip().rstrip(',').strip('"').strip("'")
                                    # Convert value types
                                    if value.lower() == 'true':
                                        value = True
                                    elif value.lower() == 'false':
                                        value = False
                                    elif value.replace('.', '').replace('-', '').isdigit():
                                        try:
                                            if '.' in value:
                                                value = float(value)
                                            else:
                                                value = int(value)
                                        except:
                                            pass
                                    mutationInput[key] = value
                            variables["input"] = mutationInput
                
                model = None
                if models and mutationName:
                    # Extract table name from mutation (e.g., "createProduct" -> "product" -> "products")
                    # Remove "create", "update", "delete" prefix
                    mutationType = None
                    if mutationName.lower().startswith("create"):
                        mutationType = "create"
                        baseName = mutationName[6:]  # Remove "create"
                    elif mutationName.lower().startswith("update"):
                        mutationType = "update"
                        baseName = mutationName[6:]  # Remove "update"
                    elif mutationName.lower().startswith("delete"):
                        mutationType = "delete"
                        baseName = mutationName[6:]  # Remove "delete"
                    else:
                        baseName = mutationName
                    
                    # Try to match with table names (e.g., "Product" -> "products", "product" -> "products")
                    for m in models:
                        tableName = m.getTableName().lower()
                        baseNameLower = baseName.lower()
                        # Check if base name matches table name (with or without 's' suffix)
                        if (baseNameLower == tableName or 
                            baseNameLower == tableName.rstrip('s') or 
                            baseNameLower + 's' == tableName or
                            tableName in baseNameLower):
                            model = m
                            break
                
                if model:
                    result = await resolveMutation(
                        mutationName,
                        model,
                        databaseManager,
                        **variables
                    )
                    # GraphQL mutations should return data in format: {"data": {"createProduct": {...}}}
                    # Use the original mutation name as the key
                    return JSONResponse({"data": {mutationName: result}})
                else:
                    return JSONResponse({"error": f"Model not found for mutation: {mutationName}"}, status_code=400)

            return JSONResponse({"error": "Invalid GraphQL query"}, status_code=400)

        except Exception as e:
            return JSONResponse(
                {"error": f"GraphQL operation failed: {str(e)}"},
                status_code=500
            )

    return Route("/graphql", graphqlHandler, methods=["GET", "POST"])

