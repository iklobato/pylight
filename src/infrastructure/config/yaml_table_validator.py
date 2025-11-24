"""YAML table configuration validator."""

from typing import Any, Dict, List, Optional

from src.domain.errors import ConfigurationError


class YAMLTableValidator:
    """Validates YAML table configuration schema."""

    VALID_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE"]

    @staticmethod
    def validateStructure(config: Dict[str, Any]) -> None:
        """Validate top-level YAML structure.

        Args:
            config: Configuration dictionary from YAML

        Raises:
            ConfigurationError: If required fields are missing
        """
        if not isinstance(config, dict):
            actualType = type(config).__name__
            raise ConfigurationError(
                f"Validation error in root: configuration must be a dictionary, got {actualType}"
            )

        if "database" not in config:
            raise ConfigurationError("Validation error in root: missing required field 'database'")
        if not isinstance(config["database"], dict):
            actualType = type(config["database"]).__name__
            raise ConfigurationError(
                f"Validation error in database: field 'database' must be a dictionary, got {actualType}"
            )
        if "url" not in config["database"]:
            raise ConfigurationError("Validation error in database: missing required field 'url'")

        if "tables" not in config:
            raise ConfigurationError("Validation error in root: missing required field 'tables'")
        if not isinstance(config["tables"], list):
            actualType = type(config["tables"]).__name__
            raise ConfigurationError(
                f"Validation error in tables: field 'tables' must be a list, got {actualType}"
            )
        if len(config["tables"]) == 0:
            raise ConfigurationError("Validation error in tables: at least one table must be specified in 'tables' array")

    @staticmethod
    def validateTableConfig(tableConfig: Dict[str, Any], index: int) -> None:
        """Validate a single table configuration.

        Args:
            tableConfig: Table configuration dictionary
            index: Index of table in tables array (for error messages)

        Raises:
            ConfigurationError: If table configuration is invalid
        """
        fieldPath = f"tables[{index}]"
        if not isinstance(tableConfig, dict):
            actualType = type(tableConfig).__name__
            raise ConfigurationError(
                f"Validation error in {fieldPath}: table must be a dictionary, got {actualType}"
            )

        if "name" not in tableConfig:
            raise ConfigurationError(f"Validation error in {fieldPath}: missing required field 'name'")
        if not isinstance(tableConfig["name"], str):
            actualType = type(tableConfig["name"]).__name__
            raise ConfigurationError(
                f"Validation error in {fieldPath}.name: field 'name' must be a string, got {actualType}"
            )
        if not tableConfig["name"]:
            raise ConfigurationError(f"Validation error in {fieldPath}.name: field 'name' cannot be empty")

        if "methods" in tableConfig:
            YAMLTableValidator.validateHttpMethods(tableConfig["methods"], index, fieldPath)

        if "permissions" in tableConfig:
            YAMLTableValidator.validatePermissions(tableConfig["permissions"], index, fieldPath)

    @staticmethod
    def validateHttpMethods(methods: Any, tableIndex: int, fieldPath: str = None) -> None:
        """Validate HTTP methods list.

        Args:
            methods: HTTP methods list
            tableIndex: Index of table (for error messages)
            fieldPath: Field path for error messages (e.g., "tables[0].methods")

        Raises:
            ConfigurationError: If methods are invalid
        """
        if fieldPath is None:
            fieldPath = f"tables[{tableIndex}]"
        methodPath = f"{fieldPath}.methods"

        if not isinstance(methods, list):
            actualType = type(methods).__name__
            actualValue = repr(methods) if len(str(methods)) < 50 else f"{type(methods).__name__}(...)"
            raise ConfigurationError(
                f"Validation error in {methodPath}: field 'methods' must be a list of strings, got {actualType}. "
                f"Actual value: {actualValue}. Suggestion: Use format: methods: [\"GET\", \"POST\"]"
            )

        for i, method in enumerate(methods):
            if not isinstance(method, str):
                actualType = type(method).__name__
                actualValue = repr(method)
                raise ConfigurationError(
                    f"Validation error in {methodPath}[{i}]: HTTP method must be a string, got {actualType}. "
                    f"Actual value: {actualValue}. Suggestion: Use a string like \"GET\" or \"POST\""
                )
            if method not in YAMLTableValidator.VALID_HTTP_METHODS:
                raise ConfigurationError(
                    f"Validation error in {methodPath}[{i}]: invalid HTTP method '{method}'. "
                    f"Must be one of: {', '.join(YAMLTableValidator.VALID_HTTP_METHODS)}"
                )

    @staticmethod
    def validatePermissions(permissions: Any, tableIndex: int, fieldPath: str = None) -> None:
        """Validate permissions structure.

        Args:
            permissions: Permissions dictionary
            tableIndex: Index of table (for error messages)
            fieldPath: Field path for error messages (e.g., "tables[0]")

        Raises:
            ConfigurationError: If permissions structure is invalid
        """
        if fieldPath is None:
            fieldPath = f"tables[{tableIndex}]"
        permissionsPath = f"{fieldPath}.permissions"

        if not isinstance(permissions, dict):
            actualType = type(permissions).__name__
            raise ConfigurationError(
                f"Validation error in {permissionsPath}: field 'permissions' must be a dictionary, got {actualType}. "
                f"Suggestion: Use format: permissions: {{ \"GET\": [\"admin\"], \"POST\": [\"admin\", \"user\"] }}"
            )

        for method, roles in permissions.items():
            if method not in YAMLTableValidator.VALID_HTTP_METHODS:
                raise ConfigurationError(
                    f"Validation error in {permissionsPath}.{method}: invalid permission method '{method}'. "
                    f"Must be one of: {', '.join(YAMLTableValidator.VALID_HTTP_METHODS)}"
                )
            if not isinstance(roles, list):
                actualType = type(roles).__name__
                raise ConfigurationError(
                    f"Validation error in {permissionsPath}.{method}: permission must be a list of roles, got {actualType}. "
                    f"Suggestion: Use format: {method}: [\"admin\", \"user\"]"
                )
            for i, role in enumerate(roles):
                if not isinstance(role, str):
                    actualType = type(role).__name__
                    raise ConfigurationError(
                        f"Validation error in {permissionsPath}.{method}[{i}]: role must be a string, got {actualType}"
                    )
                if not role:
                    raise ConfigurationError(
                        f"Validation error in {permissionsPath}.{method}[{i}]: role cannot be empty"
                    )

    @staticmethod
    def validateFeatureConfig(features: Any, tableIndex: int) -> None:
        """Validate feature configuration structure.

        Args:
            features: Features dictionary
            tableIndex: Index of table (for error messages)

        Raises:
            ConfigurationError: If feature configuration is invalid
        """
        fieldPath = f"tables[{tableIndex}].features"
        if not isinstance(features, dict):
            actualType = type(features).__name__
            raise ConfigurationError(
                f"Validation error in {fieldPath}: field 'features' must be a dictionary, got {actualType}"
            )

        if "caching" in features:
            caching = features["caching"]
            if not isinstance(caching, dict):
                actualType = type(caching).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.caching: field 'caching' must be a dictionary, got {actualType}"
                )
            if "enabled" in caching and not isinstance(caching["enabled"], bool):
                actualType = type(caching["enabled"]).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.caching.enabled: field 'enabled' must be a boolean, got {actualType}"
                )

        if "pagination" in features:
            pagination = features["pagination"]
            if not isinstance(pagination, dict):
                actualType = type(pagination).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.pagination: field 'pagination' must be a dictionary, got {actualType}"
                )
            if "enabled" in pagination and not isinstance(pagination["enabled"], bool):
                actualType = type(pagination["enabled"]).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.pagination.enabled: field 'enabled' must be a boolean, got {actualType}"
                )
            if "default_page_size" in pagination:
                if not isinstance(pagination["default_page_size"], int) or pagination["default_page_size"] < 1:
                    actualType = type(pagination["default_page_size"]).__name__
                    actualValue = pagination["default_page_size"]
                    raise ConfigurationError(
                        f"Validation error in {fieldPath}.pagination.default_page_size: field 'default_page_size' must be a positive integer, got {actualType} with value {actualValue}"
                    )
            if "max_page_size" in pagination:
                if not isinstance(pagination["max_page_size"], int) or pagination["max_page_size"] < 1:
                    actualType = type(pagination["max_page_size"]).__name__
                    actualValue = pagination["max_page_size"]
                    raise ConfigurationError(
                        f"Validation error in {fieldPath}.pagination.max_page_size: field 'max_page_size' must be a positive integer, got {actualType} with value {actualValue}"
                    )

        if "filtering" in features:
            filtering = features["filtering"]
            if not isinstance(filtering, dict):
                actualType = type(filtering).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.filtering: field 'filtering' must be a dictionary, got {actualType}"
                )
            if "enabled" in filtering and not isinstance(filtering["enabled"], bool):
                actualType = type(filtering["enabled"]).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.filtering.enabled: field 'enabled' must be a boolean, got {actualType}"
                )

        if "sorting" in features:
            sorting = features["sorting"]
            if not isinstance(sorting, dict):
                actualType = type(sorting).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.sorting: field 'sorting' must be a dictionary, got {actualType}"
                )
            if "enabled" in sorting and not isinstance(sorting["enabled"], bool):
                actualType = type(sorting["enabled"]).__name__
                raise ConfigurationError(
                    f"Validation error in {fieldPath}.sorting.enabled: field 'enabled' must be a boolean, got {actualType}"
                )

    @staticmethod
    def validateAuthenticationConfig(config: Dict[str, Any], tableConfig: Dict[str, Any], tableIndex: int) -> None:
        """Validate authentication configuration.

        Args:
            config: Full configuration dictionary
            tableConfig: Table configuration dictionary
            tableIndex: Index of table (for error messages)

        Raises:
            ConfigurationError: If authentication config is invalid
        """
        authConfig = tableConfig.get("authentication", {})
        if not isinstance(authConfig, dict):
            raise ConfigurationError(f"Table at index {tableIndex} field 'authentication' must be a dictionary")

        authRequired = authConfig.get("required", False)
        if authRequired and "authentication" not in config:
            raise ConfigurationError(
                f"Table at index {tableIndex} requires authentication but no global authentication provider configured"
            )

        if "authentication" in config:
            globalAuth = config["authentication"]
            if not isinstance(globalAuth, dict):
                raise ConfigurationError("Field 'authentication' must be a dictionary")

            jwtConfig = globalAuth.get("jwt", {})
            oauth2Config = globalAuth.get("oauth2", {})

            if authRequired:
                if not jwtConfig and not oauth2Config:
                    raise ConfigurationError(
                        f"Table at index {tableIndex} requires authentication but no authentication provider (JWT or OAuth2) configured"
                    )
                if jwtConfig and "secret_key" not in jwtConfig:
                    raise ConfigurationError(
                        f"Table at index {tableIndex} requires JWT authentication but 'authentication.jwt.secret_key' is missing"
                    )
                if oauth2Config:
                    if "client_id" not in oauth2Config or "client_secret" not in oauth2Config:
                        raise ConfigurationError(
                            f"Table at index {tableIndex} requires OAuth2 authentication but 'authentication.oauth2.client_id' or 'client_secret' is missing"
                        )

    @staticmethod
    def applyDefaults(config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values to configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration dictionary with defaults applied
        """
        config = config.copy()

        if "swagger" not in config:
            config["swagger"] = {}
        if "title" not in config["swagger"]:
            config["swagger"]["title"] = "Pylight API"
        if "version" not in config["swagger"]:
            config["swagger"]["version"] = "1.0.0"
        if "description" not in config["swagger"]:
            config["swagger"]["description"] = ""

        for i, tableConfig in enumerate(config["tables"]):
            if "methods" not in tableConfig:
                tableConfig["methods"] = ["GET", "POST", "PUT", "DELETE"]

            if "features" not in tableConfig:
                tableConfig["features"] = {}
            features = tableConfig["features"]

            if "pagination" not in features:
                features["pagination"] = {}
            if "enabled" not in features["pagination"]:
                features["pagination"]["enabled"] = True
            if "default_page_size" not in features["pagination"]:
                features["pagination"]["default_page_size"] = 10
            if "max_page_size" not in features["pagination"]:
                features["pagination"]["max_page_size"] = 100

            if "filtering" not in features:
                features["filtering"] = {"enabled": True}
            elif "enabled" not in features["filtering"]:
                features["filtering"]["enabled"] = True

            if "sorting" not in features:
                features["sorting"] = {"enabled": True}
            elif "enabled" not in features["sorting"]:
                features["sorting"]["enabled"] = True

            if "graphql" not in features:
                features["graphql"] = True
            if "websocket" not in features:
                features["websocket"] = True

            if "caching" not in features:
                features["caching"] = {"enabled": True}

        return config

    @staticmethod
    def resolveInheritance(config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve authentication inheritance from global to table level.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration dictionary with inheritance resolved
        """
        config = config.copy()
        globalAuth = config.get("authentication", {})

        for tableConfig in config["tables"]:
            tableAuth = tableConfig.get("authentication", {})
            if not isinstance(tableAuth, dict):
                tableAuth = {}
                tableConfig["authentication"] = tableAuth

            if "required" not in tableAuth and globalAuth:
                tableAuth["required"] = bool(globalAuth.get("jwt") or globalAuth.get("oauth2"))

            if "roles" not in tableAuth:
                tableAuth["roles"] = []

        return config

    @staticmethod
    def validate(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize YAML configuration.

        Args:
            config: Configuration dictionary from YAML

        Returns:
            Validated and normalized configuration dictionary

        Raises:
            ConfigurationError: If configuration is invalid
        """
        YAMLTableValidator.validateStructure(config)

        for i, tableConfig in enumerate(config["tables"]):
            YAMLTableValidator.validateTableConfig(tableConfig, i)
            YAMLTableValidator.validateAuthenticationConfig(config, tableConfig, i)
            if "features" in tableConfig:
                YAMLTableValidator.validateFeatureConfig(tableConfig["features"], i)

        config = YAMLTableValidator.applyDefaults(config)
        config = YAMLTableValidator.resolveInheritance(config)

        return config

