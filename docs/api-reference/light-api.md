# LightApi

Main application class for Pylight framework.

## Class Definition

```python
class LightApi:
    """Main application class for Pylight framework."""
```

## Constructor

### `__init__`

Initialize LightApi application.

```python
def __init__(
    self,
    databaseUrl: Optional[str] = None,
    swaggerTitle: str = "Pylight API",
    swaggerVersion: str = "1.0.0",
    swaggerDescription: str = "",
    configPath: Optional[str] = None,
    configClass: Optional[Type[Any]] = None,
) -> None
```

**Parameters**:
- `databaseUrl` (Optional[str]): Database connection URL
- `swaggerTitle` (str): Swagger documentation title (default: "Pylight API")
- `swaggerVersion` (str): API version (default: "1.0.0")
- `swaggerDescription` (str): API description (default: "")
- `configPath` (Optional[str]): Path to YAML configuration file
- `configClass` (Optional[Type[Any]]): Python class for configuration

**Example**:

```python
app = LightApi(
    databaseUrl="sqlite:///app.db",
    swaggerTitle="My API",
    swaggerVersion="1.0.0"
)
```

## Class Methods

### `fromYamlConfig`

Create LightApi instance from YAML table configuration file.

```python
@classmethod
def fromYamlConfig(cls, yamlPath: str) -> "LightApi"
```

**Parameters**:
- `yamlPath` (str): Path to YAML configuration file

**Returns**:
- `LightApi`: LightApi instance with all tables registered and configured

**Raises**:
- `ConfigurationError`: If YAML configuration is invalid
- `ReflectionError`: If database reflection fails

**Example**:

```python
app = LightApi.fromYamlConfig("config.yaml")
app.run(host="localhost", port=8000)
```

## Instance Methods

### `register`

Register a model class for automatic endpoint generation.

```python
def register(self, model: Type[RestEndpoint]) -> None
```

**Parameters**:
- `model` (Type[RestEndpoint]): Model class inheriting from RestEndpoint

**Raises**:
- `ConfigurationError`: If model does not inherit from RestEndpoint

**Example**:

```python
app.register(Product)
```

### `addMiddleware`

Add middleware to the application.

```python
def addMiddleware(self, middleware: List[Any]) -> None
```

**Parameters**:
- `middleware` (List[Any]): List of middleware classes

**Example**:

```python
app.addMiddleware([LoggingMiddleware, AuthMiddleware])
```

### `registerPlugin`

Register a plugin with the application.

```python
def registerPlugin(self, pluginClass: Type[Any]) -> None
```

**Parameters**:
- `pluginClass` (Type[Any]): Plugin class to register

**Example**:

```python
app.registerPlugin(HealthCheckPlugin)
```

### `run`

Run the application server.

```python
def run(self, host: str = "localhost", port: int = 8000, debug: bool = False) -> None
```

**Parameters**:
- `host` (str): Host to bind to (default: "localhost")
- `port` (int): Port to bind to (default: 8000)
- `debug` (bool): Enable debug mode (default: False)

**Example**:

```python
app.run(host="0.0.0.0", port=8000, debug=True)
```

## Attributes

- `databaseUrl` (Optional[str]): Database connection URL
- `swaggerTitle` (str): Swagger documentation title
- `swaggerVersion` (str): API version
- `swaggerDescription` (str): API description
- `registeredModels` (List[Type[RestEndpoint]]): List of registered models
- `middleware` (List[Any]): List of middleware
- `pluginRegistry` (PluginRegistry): Plugin registry
- `databaseManager` (Optional[DatabaseManager]): Database manager
- `starletteApp` (Starlette): Starlette application instance

## Examples

### Basic Usage

```python
from pylight.presentation.app import LightApi
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String

class Product(RestEndpoint):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

app = LightApi(databaseUrl="sqlite:///app.db")
app.register(Product)
app.run(host="localhost", port=8000)
```

### YAML Configuration

```python
app = LightApi.fromYamlConfig("config.yaml")
app.run(host="localhost", port=8000)
```

## Next Steps

- Learn about [RestEndpoint](rest-endpoint.md) for model definition
- Explore [Configuration Options](configuration-options.md) for setup

