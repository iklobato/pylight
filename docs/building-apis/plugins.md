# Plugins

Pylight's plugin system allows you to extend framework functionality with custom code, enabling advanced customization and integration with external systems.

## Overview

Plugins provide:

- **Custom Functionality**: Add features beyond core framework
- **Integration Points**: Integrate with external services
- **Reusable Components**: Share functionality across projects
- **Lifecycle Hooks**: Initialize and register custom code

## Basic Plugin Structure

A plugin is a class that implements the `Plugin` interface:

```python
from pylight.domain.plugins.interface import Plugin
from pylight.presentation.app import LightApi

class MyPlugin(Plugin):
    def initialize(self, app: LightApi):
        """Initialize plugin with app instance."""
        pass
    
    def register(self, app: LightApi):
        """Register routes, middleware, or other functionality."""
        pass
```

## Plugin Lifecycle

1. **Initialization**: `initialize()` is called when the app starts
2. **Registration**: `register()` is called after models are registered
3. **Execution**: Plugin functionality is available during request handling

## Example: Custom Route Plugin

Add custom routes:

```python
from pylight.domain.plugins.interface import Plugin
from pylight.presentation.app import LightApi
from starlette.routing import Route
from starlette.responses import JSONResponse

class HealthCheckPlugin(Plugin):
    def initialize(self, app: LightApi):
        """Initialize health check plugin."""
        self.app = app
    
    def register(self, app: LightApi):
        """Register health check route."""
        async def health_check(request):
            return JSONResponse({"status": "healthy"})
        
        app.starletteApp.routes.append(
            Route("/health", health_check, methods=["GET"])
        )
```

## Example: Middleware Plugin

Add custom middleware:

```python
from pylight.domain.plugins.interface import Plugin
from pylight.presentation.app import LightApi
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingPlugin(Plugin):
    def initialize(self, app: LightApi):
        """Initialize logging plugin."""
        self.app = app
    
    def register(self, app: LightApi):
        """Register logging middleware."""
        class LoggingMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                print(f"Request: {request.method} {request.url}")
                response = await call_next(request)
                print(f"Response: {response.status_code}")
                return response
        
        app.starletteApp.middleware_stack = LoggingMiddleware(app.starletteApp)
```

## Registering Plugins

### Programmatic Registration

```python
from pylight.presentation.app import LightApi

app = LightApi(databaseUrl="sqlite:///app.db")
app.registerPlugin(HealthCheckPlugin)
app.registerPlugin(LoggingPlugin)
app.run(host="localhost", port=8000)
```

### Multiple Plugins

```python
app.registerPlugin(HealthCheckPlugin)
app.registerPlugin(LoggingPlugin)
app.registerPlugin(CustomAuthPlugin)
```

## Plugin Examples

### Metrics Plugin

Collect API metrics:

```python
from pylight.domain.plugins.interface import Plugin
from pylight.presentation.app import LightApi
from starlette.routing import Route
from starlette.responses import JSONResponse

class MetricsPlugin(Plugin):
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
    
    def initialize(self, app: LightApi):
        self.app = app
    
    def register(self, app: LightApi):
        # Add metrics endpoint
        async def metrics(request):
            return JSONResponse({
                "requests": self.request_count,
                "errors": self.error_count
            })
        
        app.starletteApp.routes.append(
            Route("/metrics", metrics, methods=["GET"])
        )
        
        # Add middleware to track metrics
        # (Implementation details omitted)
```

### External Service Integration

Integrate with external services:

```python
class ExternalServicePlugin(Plugin):
    def initialize(self, app: LightApi):
        # Initialize external service client
        self.client = ExternalServiceClient()
    
    def register(self, app: LightApi):
        # Register routes that use external service
        async def external_data(request):
            data = await self.client.fetch_data()
            return JSONResponse(data)
        
        app.starletteApp.routes.append(
            Route("/external", external_data, methods=["GET"])
        )
```

## Best Practices

1. **Single Responsibility**: Each plugin should have one clear purpose
2. **Idempotent**: Plugins should be safe to register multiple times
3. **Documentation**: Document plugin behavior and configuration
4. **Error Handling**: Handle errors gracefully
5. **Testing**: Test plugins in isolation

## Plugin Registry

Pylight maintains a plugin registry that:

- **Tracks Plugins**: Keeps list of registered plugins
- **Initializes Plugins**: Calls `initialize()` on all plugins
- **Registers Plugins**: Calls `register()` after model registration

## Advanced Usage

### Plugin Configuration

Pass configuration to plugins:

```python
class ConfigurablePlugin(Plugin):
    def __init__(self, config: dict):
        self.config = config
    
    def initialize(self, app: LightApi):
        # Use self.config
        pass
```

### Plugin Dependencies

Plugins can depend on other plugins:

```python
class DependentPlugin(Plugin):
    def initialize(self, app: LightApi):
        # Access other plugins via app.pluginRegistry
        pass
```

## Troubleshooting

### Plugin Not Executing

Ensure plugin is registered before `app.run()`:

```python
app.registerPlugin(MyPlugin)  # Before app.run()
app.run(host="localhost", port=8000)
```

### Plugin Errors

Check plugin initialization and registration:

```python
try:
    plugin.initialize(app)
    plugin.register(app)
except Exception as e:
    print(f"Plugin error: {e}")
```

## Examples

For complete plugin examples, see:
- [Plugin Examples](https://github.com/iklobato/pylight/tree/main/docs/examples)
- [Use Cases](../use-cases/index.md) for real-world patterns

## Next Steps

- Learn about [Customization](../customization/index.md) for advanced customization
- Explore [Middleware](../customization/middleware.md) for request/response handling
- Check out [Use Cases](../use-cases/index.md) for real-world examples

