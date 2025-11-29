"""YAML table configuration loader and model generator."""

from typing import Any, Dict, List, Optional, Type
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import DeclarativeBase

from src.domain.entities.rest_endpoint import RestEndpoint
from src.domain.errors import ConfigurationError, ReflectionError
from src.infrastructure.config.yaml_loader import YAMLLoader
from src.infrastructure.config.yaml_table_validator import YAMLTableValidator
from src.infrastructure.database.reflection import DatabaseReflection
from src.infrastructure.database.connection import DatabaseManager


class YAMLTableConfigLoader:
    """Loads YAML table configuration and generates models dynamically."""

    def __init__(self, yamlPath: str) -> None:
        """Initialize YAML table config loader.

        Args:
            yamlPath: Path to YAML configuration file
        """
        self.yamlPath = yamlPath
        self.config: Optional[Dict[str, Any]] = None
        self.databaseManager: Optional[DatabaseManager] = None
        self.reflection: Optional[DatabaseReflection] = None

    def loadYamlConfig(self) -> Dict[str, Any]:
        """Load and parse YAML configuration file.

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If YAML file cannot be loaded or parsed
        """
        try:
            rawConfig = YAMLLoader.load(self.yamlPath)
            self.config = YAMLTableValidator.validate(rawConfig)
            return self.config
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Error loading YAML configuration: {e}") from e

    def validateConfig(self) -> None:
        """Validate YAML configuration schema.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if self.config is None:
            raise ConfigurationError("Configuration not loaded. Call loadYamlConfig() first.")
        YAMLTableValidator.validate(self.config)

    def validateTablesExist(self) -> None:
        """Validate that all tables specified in YAML exist in database.

        Raises:
            ConfigurationError: If any tables are missing
            ReflectionError: If database connection or reflection fails
        """
        if self.config is None:
            raise ConfigurationError("Configuration not loaded. Call loadYamlConfig() first.")

        databaseUrl = self.config["database"]["url"]
        try:
            DatabaseManager.convertToAsyncUrl(databaseUrl)
        except ConfigurationError as e:
            raise ConfigurationError(
                f"Invalid database URL in configuration: {e}"
            ) from e
        self.reflection = DatabaseReflection(databaseUrl)
        existingTables = self.reflection.reflectTables()

        missingTables = []
        for tableConfig in self.config["tables"]:
            tableName = tableConfig["name"]
            if tableName not in existingTables:
                missingTables.append(tableName)

        if missingTables:
            availableTablesStr = ", ".join(existingTables) if existingTables else "none"
            raise ConfigurationError(
                f"Tables not found in database: {', '.join(missingTables)}. "
                f"Available tables: {availableTablesStr}"
            )

    def reflectTables(self) -> List[Dict[str, Any]]:
        """Reflect all configured tables from database.

        Returns:
            List of table reflection dictionaries

        Raises:
            ReflectionError: If reflection fails for any table
        """
        if self.config is None or self.reflection is None:
            raise ConfigurationError("Configuration and reflection not initialized")

        tableInfos = []
        for tableConfig in self.config["tables"]:
            tableName = tableConfig["name"]
            try:
                tableInfo = self.reflection.reflectTable(tableName)
                tableInfos.append(tableInfo)
            except ReflectionError as e:
                raise ReflectionError(f"Failed to reflect table '{tableName}': {e}") from e

        return tableInfos

    def _mapColumnType(self, sqlType: Any) -> Type[Any]:
        """Map SQLAlchemy column type from reflection to Column type.

        Args:
            sqlType: SQLAlchemy type from reflection

        Returns:
            SQLAlchemy Column type class
        """
        typeStr = str(sqlType).lower()
        if "int" in typeStr:
            return Integer
        elif "varchar" in typeStr or "text" in typeStr or "string" in typeStr or "char" in typeStr:
            return String
        elif "datetime" in typeStr or "timestamp" in typeStr:
            return DateTime
        elif "bool" in typeStr:
            return Boolean
        elif "float" in typeStr or "decimal" in typeStr or "numeric" in typeStr:
            return Float
        elif "json" in typeStr:
            # Use JSONB for better performance, JSON as fallback
            if "jsonb" in typeStr:
                return JSONB
            return JSON
        else:
            return String

    def _toPascalCase(self, snakeStr: str) -> str:
        """Convert snake_case to PascalCase.

        Args:
            snakeStr: Snake case string

        Returns:
            PascalCase string
        """
        components = snakeStr.split("_")
        return "".join(word.capitalize() for word in components)

    def generateModels(self) -> List[Type[RestEndpoint]]:
        """Generate RestEndpoint subclasses dynamically from reflected tables.

        Returns:
            List of dynamically generated model classes

        Raises:
            ConfigurationError: If configuration or reflection not initialized
        """
        if self.config is None:
            raise ConfigurationError("Configuration not loaded. Call loadYamlConfig() first.")

        tableInfos = self.reflectTables()
        models = []

        for tableInfo, tableConfig in zip(tableInfos, self.config["tables"]):
            tableName = tableInfo["name"]
            className = self._toPascalCase(tableName)

            attrs = {
                "__tablename__": tableName,
                "__doc__": f"Model for {tableName} table (generated from YAML)",
            }

            for col in tableInfo["columns"]:
                colName = col["name"]
                colType = self._mapColumnType(col["type"])
                nullable = col.get("nullable", True)
                primaryKey = colName in tableInfo["primary_key"].get("constrained_columns", [])
                serverDefault = col.get("server_default")

                colKwargs = {}
                if not nullable:
                    colKwargs["nullable"] = False
                if primaryKey:
                    colKwargs["primary_key"] = True
                # Set server_default if it exists (for timestamp columns with now() default)
                if serverDefault:
                    from sqlalchemy import text
                    # server_default comes as a string like "now()" or a FetchedValue
                    if isinstance(serverDefault, str):
                        colKwargs["server_default"] = text(serverDefault)
                    else:
                        colKwargs["server_default"] = serverDefault

                if "varchar" in str(col["type"]).lower() or "char" in str(col["type"]).lower():
                    length = col.get("type").length if hasattr(col.get("type"), "length") else None
                    if length:
                        attrs[colName] = Column(colType(length), **colKwargs)
                    else:
                        attrs[colName] = Column(colType, **colKwargs)
                else:
                    attrs[colName] = Column(colType, **colKwargs)

            modelClass = type(className, (RestEndpoint,), attrs)
            self.applyTableConfig(modelClass, tableConfig)
            models.append(modelClass)

        return models

    def loadAuthenticationConfig(self) -> Dict[str, Any]:
        """Load global authentication provider settings from YAML.

        Returns:
            Dictionary with authentication configuration
        """
        if self.config is None:
            return {}
        return self.config.get("authentication", {})

    def applyAuthenticationConfig(self, modelClass: Type[RestEndpoint], tableConfig: Dict[str, Any]) -> None:
        """Apply authentication configuration per table (inherit from global or override).

        Args:
            modelClass: Model class to configure
            tableConfig: Table configuration from YAML
        """
        globalAuth = self.loadAuthenticationConfig()
        tableAuth = tableConfig.get("authentication", {})

        authRequired = tableAuth.get("required", False)
        if not authRequired and globalAuth:
            authRequired = bool(globalAuth.get("jwt") or globalAuth.get("oauth2"))

        if authRequired:
            if globalAuth.get("jwt"):
                from src.infrastructure.auth.jwt import DefaultJWTAuthentication
                secretKey = globalAuth["jwt"].get("secret_key")
                if secretKey:
                    def initAuth(self):
                        DefaultJWTAuthentication.__init__(self, secretKey)

                    authClass = type(
                        "JWTAuth",
                        (DefaultJWTAuthentication,),
                        {"__init__": initAuth}
                    )
                    modelClass.Configuration.authentication_class = authClass
            elif globalAuth.get("oauth2"):
                from src.infrastructure.auth.oauth2 import DefaultOAuth2Authentication
                clientId = globalAuth["oauth2"].get("client_id")
                clientSecret = globalAuth["oauth2"].get("client_secret")
                if clientId and clientSecret:
                    def initAuth(self):
                        DefaultOAuth2Authentication.__init__(self, clientId, clientSecret)

                    authClass = type(
                        "OAuth2Auth",
                        (DefaultOAuth2Authentication,),
                        {"__init__": initAuth}
                    )
                    modelClass.Configuration.authentication_class = authClass

    def applyPermissionsConfig(self, modelClass: Type[RestEndpoint], tableConfig: Dict[str, Any]) -> None:
        """Configure required roles per HTTP method per table.

        Args:
            modelClass: Model class to configure
            tableConfig: Table configuration from YAML
        """
        permissions = tableConfig.get("permissions", {})
        if permissions:
            modelClass.Configuration.required_roles = permissions.copy()

    def loadFeaturesConfig(self, tableConfig: Dict[str, Any]) -> Dict[str, Any]:
        """Load feature settings per table from YAML.

        Args:
            tableConfig: Table configuration from YAML

        Returns:
            Dictionary with feature configuration
        """
        return tableConfig.get("features", {})

    def applyCachingConfig(self, modelClass: Type[RestEndpoint], tableConfig: Dict[str, Any]) -> None:
        """Configure caching per table (enable/disable, set caching_class).

        Args:
            modelClass: Model class to configure
            tableConfig: Table configuration from YAML
        """
        features = self.loadFeaturesConfig(tableConfig)
        caching = features.get("caching", {})
        enabled = caching.get("enabled", True)

        if enabled:
            try:
                from src.infrastructure.cache.redis import DefaultRedisCache
                import os
                redisUrl = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                cacheClass = type(
                    "RedisCache",
                    (DefaultRedisCache,),
                    {"__init__": lambda self: DefaultRedisCache.__init__(self, redisUrl)}
                )
                modelClass.Configuration.caching_class = cacheClass
                modelClass.Configuration.caching_method_names = ["GET"]
            except Exception:
                pass

    def applyPaginationConfig(self, modelClass: Type[RestEndpoint], tableConfig: Dict[str, Any]) -> None:
        """Configure pagination settings (default_page_size, max_page_size) per table.

        Args:
            modelClass: Model class to configure
            tableConfig: Table configuration from YAML
        """
        features = self.loadFeaturesConfig(tableConfig)
        pagination = features.get("pagination", {})
        enabled = pagination.get("enabled", True)

        if enabled:
            from src.shared.pagination.paginator import DefaultPaginator
            defaultPageSize = pagination.get("default_page_size", 10)
            maxPageSize = pagination.get("max_page_size", 100)

            class CustomPaginator(DefaultPaginator):
                def __init__(self, request):
                    super().__init__(request)
                    self.defaultPageSize = defaultPageSize
                    self.maxPageSize = maxPageSize

            modelClass.Configuration.pagination_class = CustomPaginator

    def applyFilteringConfig(self, modelClass: Type[RestEndpoint], tableConfig: Dict[str, Any]) -> None:
        """Enable/disable filtering per table.

        Args:
            modelClass: Model class to configure
            tableConfig: Table configuration from YAML
        """
        features = self.loadFeaturesConfig(tableConfig)
        filtering = features.get("filtering", {})
        enabled = filtering.get("enabled", True)
        modelClass._filtering_enabled = enabled

    def applySortingConfig(self, modelClass: Type[RestEndpoint], tableConfig: Dict[str, Any]) -> None:
        """Enable/disable sorting per table.

        Args:
            modelClass: Model class to configure
            tableConfig: Table configuration from YAML
        """
        features = self.loadFeaturesConfig(tableConfig)
        sorting = features.get("sorting", {})
        enabled = sorting.get("enabled", True)
        modelClass._sorting_enabled = enabled

    def applyTableConfig(self, modelClass: Type[RestEndpoint], tableConfig: Dict[str, Any]) -> None:
        """Apply table configuration to model class (HTTP methods, auth, features).

        Args:
            modelClass: Model class to configure
            tableConfig: Table configuration from YAML
        """
        methods = tableConfig.get("methods", ["GET", "POST", "PUT", "DELETE"])
        modelClass._allowed_methods = methods
        modelClass._table_config = tableConfig

        self.applyAuthenticationConfig(modelClass, tableConfig)
        self.applyPermissionsConfig(modelClass, tableConfig)
        self.applyCachingConfig(modelClass, tableConfig)
        self.applyPaginationConfig(modelClass, tableConfig)
        self.applyFilteringConfig(modelClass, tableConfig)
        self.applySortingConfig(modelClass, tableConfig)

    def registerModels(self, app: Any) -> None:
        """Register all generated models with LightApi.

        Args:
            app: LightApi instance

        Raises:
            ConfigurationError: If models not generated
        """
        if self.config is None:
            raise ConfigurationError("Configuration not loaded")

        databaseUrl = self.config["database"]["url"]
        try:
            DatabaseManager.convertToAsyncUrl(databaseUrl)
        except ConfigurationError as e:
            raise ConfigurationError(
                f"Invalid database URL in configuration: {e}"
            ) from e
        self.databaseManager = DatabaseManager(databaseUrl, asyncMode=True)
        app.databaseManager = self.databaseManager

        if "swagger" in self.config:
            swaggerConfig = self.config["swagger"]
            if "title" in swaggerConfig:
                app.swaggerTitle = swaggerConfig["title"]
            if "version" in swaggerConfig:
                app.swaggerVersion = swaggerConfig["version"]
            if "description" in swaggerConfig:
                app.swaggerDescription = swaggerConfig["description"]

        models = self.generateModels()
        for model in models:
            allowedMethods = getattr(model, "_allowed_methods", ["GET", "POST", "PUT", "DELETE"])
            self._registerModelWithMethods(app, model, allowedMethods)

    def load(self) -> Dict[str, Any]:
        """Load, validate, and prepare configuration.

        Returns:
            Validated configuration dictionary

        Raises:
            ConfigurationError: If configuration is invalid
            ReflectionError: If database reflection fails
        """
        self.loadYamlConfig()
        self.validateConfig()
        self.validateTablesExist()
        return self.config

    def _registerModelWithMethods(self, app: Any, model: Type[RestEndpoint], allowedMethods: List[str]) -> None:
        """Register model with LightApi, filtering routes by allowed methods.

        Args:
            app: LightApi instance
            model: Model class to register
            allowedMethods: List of allowed HTTP methods
        """
        from src.application.endpoints.rest_generator import RESTGenerator
        from src.presentation.graphql.router import createGraphQLRoute
        from src.presentation.websocket.handler import createWebSocketRoute
        from src.presentation.docs.graphiql import createGraphiQLRoute

        if not hasattr(model, "__subclasscheck__"):
            if not issubclass(model, RestEndpoint):
                raise ConfigurationError(f"{model.__name__} must inherit from RestEndpoint")

        app.registeredModels.append(model)

        allRoutes = RESTGenerator.generateRoutes(model, self.databaseManager)
        filteredRoutes = [
            route for route in allRoutes
            if route.methods and any(method in allowedMethods for method in route.methods)
        ]
        app.starletteApp.routes.extend(filteredRoutes)

        graphqlRoute = createGraphQLRoute(self.databaseManager, app.registeredModels)
        if not any(r.path == "/graphql" for r in app.starletteApp.routes):
            app.starletteApp.routes.append(graphqlRoute)

        graphiqlRoute = createGraphiQLRoute()
        if not any(r.path == "/graphiql" for r in app.starletteApp.routes):
            app.starletteApp.routes.append(graphiqlRoute)

        websocketRoute = createWebSocketRoute(model)
        app.starletteApp.routes.append(websocketRoute)

