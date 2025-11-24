"""GraphiQL interface generator."""

from starlette.routing import Route
from starlette.responses import HTMLResponse


def createGraphiQLRoute() -> Route:
    """Create GraphiQL interface route.

    Returns:
        Starlette Route for GraphiQL
    """
    graphiqlHtml = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GraphiQL</title>
        <link rel="stylesheet" href="https://unpkg.com/graphiql@latest/graphiql.min.css" />
    </head>
    <body>
        <div id="graphiql">Loading...</div>
        <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/graphiql@latest/graphiql.min.js"></script>
        <script>
            const graphQLFetcher = graphQLParams =>
                fetch('/graphql', {
                    method: 'post',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(graphQLParams),
                })
                .then(response => response.json());
            ReactDOM.render(
                React.createElement(GraphiQL, { fetcher: graphQLFetcher }),
                document.getElementById('graphiql'),
            );
        </script>
    </body>
    </html>
    """

    async def graphiqlHandler(request):
        """Handle GraphiQL requests."""
        return HTMLResponse(graphiqlHtml)

    return Route("/graphiql", graphiqlHandler, methods=["GET"])

