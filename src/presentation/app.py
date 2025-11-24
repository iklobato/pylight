"""Starlette application wrapper and LightApi main class."""

from typing import Any, Dict, List, Optional, Type
from starlette.applications import Starlette
from starlette.middleware import Middleware as StarletteMiddleware
from starlette.routing import Route, WebSocketRoute
from starlette.responses import JSONResponse
import uvicorn

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ConfigurationError, DatabaseError
from src.infrastructure.config.yaml_loader import YAMLLoader
from src.infrastructure.config.class_loader import ClassLoader
from src.infrastructure.config.merger import ConfigMerger
from src.infrastructure.config.validator import ConfigValidator
from src.infrastructure.database.connection import DatabaseManager
from src.infrastructure.plugins.registry import PluginRegistry
from src.presentation.rest.error_handler import handleError
from src.application.endpoints.rest_generator import RESTGenerator
from src.presentation.graphql.router import createGraphQLRoute
from src.presentation.websocket.handler import createWebSocketRoute
from src.presentation.docs.openapi import OpenAPIGenerator
from src.presentation.docs.graphiql import createGraphiQLRoute


class LightApi:
    """Main application class for Pylight framework."""

    def __init__(
        self,
        databaseUrl: Optional[str] = None,
        swaggerTitle: str = "Pylight API",
        swaggerVersion: str = "1.0.0",
        swaggerDescription: str = "",
        configPath: Optional[str] = None,
        configClass: Optional[Type[Any]] = None,
    ) -> None:
        """Initialize LightApi application.

        Args:
            databaseUrl: Database connection URL
            swaggerTitle: Swagger documentation title
            swaggerVersion: API version
            swaggerDescription: API description
            configPath: Path to YAML configuration file
            configClass: Python class for configuration
        """
        self.databaseUrl = databaseUrl
        self.swaggerTitle = swaggerTitle
        self.swaggerVersion = swaggerVersion
        self.swaggerDescription = swaggerDescription
        self.registeredModels: List[Type[RestEndpoint]] = []
        self.middleware: List[Any] = []
        self.pluginRegistry = PluginRegistry()
        self.databaseManager: Optional[DatabaseManager] = None

        self.config = self._loadConfiguration(configPath, configClass)

        if self.config.get("database", {}).get("url"):
            self.databaseUrl = self.config["database"]["url"]

        if self.config.get("swagger", {}).get("title"):
            self.swaggerTitle = self.config["swagger"]["title"]

        if self.config.get("swagger", {}).get("version"):
            self.swaggerVersion = self.config["swagger"]["version"]

        if self.databaseUrl:
            try:
                self.databaseManager = DatabaseManager(self.databaseUrl, asyncMode=True)
            except Exception as e:
                raise DatabaseError(f"Failed to initialize database connection: {e}") from e

        self.starletteApp = Starlette(
            routes=[],
            middleware=[],
            exception_handlers={Exception: handleError},
        )

        self._initializePlugins()

    @classmethod
    def fromYamlConfig(cls, yamlPath: str) -> "LightApi":
        """Create LightApi instance from YAML table configuration file.

        Args:
            yamlPath: Path to YAML configuration file

        Returns:
            LightApi instance with all tables registered and configured

        Raises:
            ConfigurationError: If YAML configuration is invalid
            ReflectionError: If database reflection fails
        """
        from src.application.config.yaml_table_loader import YAMLTableConfigLoader

        loader = YAMLTableConfigLoader(yamlPath)
        config = loader.load()

        databaseUrl = config["database"]["url"]
        swaggerTitle = config.get("swagger", {}).get("title", "Pylight API")
        swaggerVersion = config.get("swagger", {}).get("version", "1.0.0")
        swaggerDescription = config.get("swagger", {}).get("description", "")

        app = cls(
            databaseUrl=databaseUrl,
            swaggerTitle=swaggerTitle,
            swaggerVersion=swaggerVersion,
            swaggerDescription=swaggerDescription,
        )

        loader.registerModels(app)
        return app

    def _loadConfiguration(
        self, configPath: Optional[str], configClass: Optional[Type[Any]]
    ) -> Dict[str, Any]:
        """Load configuration from YAML or class.

        Args:
            configPath: Path to YAML file
            configClass: Configuration class

        Returns:
            Configuration dictionary
        """
        configs: List[Dict[str, Any]] = []

        if configPath:
            yamlConfig = YAMLLoader.load(configPath)
            configs.append(yamlConfig)

        if configClass:
            classConfig = ClassLoader.load(configClass)
            configs.append(classConfig)

        merged = ConfigMerger.merge(*configs)
        return ConfigValidator.validate(merged)

    def register(self, model: Type[RestEndpoint]) -> None:
        """Register a model class for automatic endpoint generation.

        Args:
            model: Model class inheriting from RestEndpoint
        """
        if not issubclass(model, RestEndpoint):
            raise ConfigurationError(f"{model.__name__} must inherit from RestEndpoint")
        self.registeredModels.append(model)

        restRoutes = RESTGenerator.generateRoutes(model, self.databaseManager)
        self.starletteApp.routes.extend(restRoutes)

        graphqlRoute = createGraphQLRoute(self.databaseManager, self.registeredModels)
        if not any(r.path == "/graphql" for r in self.starletteApp.routes):
            self.starletteApp.routes.append(graphqlRoute)

        graphiqlRoute = createGraphiQLRoute()
        if not any(r.path == "/graphiql" for r in self.starletteApp.routes):
            self.starletteApp.routes.append(graphiqlRoute)

        websocketRoute = createWebSocketRoute(model)
        self.starletteApp.routes.append(websocketRoute)

        openapiGenerator = OpenAPIGenerator(
            self.swaggerTitle, self.swaggerVersion, self.swaggerDescription
        )
        openapiSpec = openapiGenerator.generate(self.registeredModels, self.starletteApp.routes)

        async def openapiHandler(request):
            """Handle OpenAPI/Swagger documentation requests."""
            return JSONResponse(openapiSpec)

        async def docsHandler(request):
            """Handle Swagger UI requests."""
            swaggerHtml = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{self.swaggerTitle}</title>
                <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@latest/swagger-ui.css" />
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script src="https://unpkg.com/swagger-ui-dist@latest/swagger-ui-bundle.js"></script>
                <script>
                    SwaggerUIBundle({{
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                    }});
                </script>
            </body>
            </html>
            """
            from starlette.responses import HTMLResponse
            return HTMLResponse(swaggerHtml)

        if not any(r.path == "/openapi.json" for r in self.starletteApp.routes):
            self.starletteApp.routes.append(Route("/openapi.json", openapiHandler, methods=["GET"]))
        if not any(r.path == "/docs" for r in self.starletteApp.routes):
            self.starletteApp.routes.append(Route("/docs", docsHandler, methods=["GET"]))

    def addMiddleware(self, middleware: List[Any]) -> None:
        """Add middleware to the application.

        Args:
            middleware: List of middleware classes
        """
        self.middleware.extend(middleware)

    def registerPlugin(self, pluginClass: Type[Any]) -> None:
        """Register a plugin with the application.

        Args:
            pluginClass: Plugin class to register
        """
        self.pluginRegistry.register(pluginClass)

    def _initializePlugins(self) -> None:
        """Initialize all registered plugins."""
        self.pluginRegistry.initialize(self)

    def run(self, host: str = "localhost", port: int = 8000, debug: bool = False) -> None:
        """Run the application server.

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        uvicorn.run(self.starletteApp, host=host, port=port, log_level="debug" if debug else "info")

