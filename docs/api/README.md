# Pylight API Reference

## Core Classes

### LightApi

Main application class for Pylight framework.

**Methods**:
- `__init__(database_url, swagger_title, swagger_version, swagger_description, config_path, config_class)`: Initialize application
- `register(model)`: Register a model for automatic endpoint generation
- `add_middleware(middleware)`: Add middleware to the application
- `register_plugin(plugin_class)`: Register a plugin
- `run(host, port, debug)`: Run the application server

### RestEndpoint

Base class for all models/endpoints.

**Attributes**:
- Inherits SQLAlchemy declarative base
- Table name derived from class name (lowercase)

**Configuration**:
- Nested `Configuration` class for endpoint-level settings

## Authentication

### JWTAuthentication

Base class for JWT authentication. Extend to customize.

### OAuth2Authentication

Base class for OAuth2 authentication. Extend to customize.

## Caching

### RedisCache

Base class for Redis caching. Extend to customize.

## Pagination

### Paginator

Base class for pagination. Extend to customize.

## Middleware

### Middleware

Base class for middleware. Extend to customize.

## Plugins

### Plugin

Base class for plugins. Implement `initialize()` and `register()` methods.

