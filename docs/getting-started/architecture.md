# Architecture

Pylight follows a clean, layered architecture that separates concerns and enables maintainability and extensibility.

## Overview

Pylight is organized into four main layers:

```
┌─────────────────────────────────────┐
│      Presentation Layer             │
│  (REST, GraphQL, WebSocket)         │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│      Application Layer              │
│  (Endpoint Generation, Orchestration)│
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│      Domain Layer                   │
│  (Business Logic, Entities)         │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│      Infrastructure Layer           │
│  (Database, Cache, Auth, Config)     │
└─────────────────────────────────────┘
```

## Layer Details

### Domain Layer

**Location**: `src/domain/`

**Purpose**: Contains business logic and core entities.

**Components**:
- **Entities**: Base classes like `RestEndpoint` that define the model structure
- **Errors**: Domain-specific error types (`ConfigurationError`, `DatabaseError`, etc.)
- **Plugins**: Plugin interface definitions
- **Validators**: Base validation logic

**Key Classes**:
- `RestEndpoint`: Base class for all API models
- `PylightError`: Base exception class
- `Plugin`: Plugin interface

**Dependencies**: None (domain does not depend on infrastructure)

### Application Layer

**Location**: `src/application/`

**Purpose**: Orchestrates endpoint generation and business workflows.

**Components**:
- **Endpoints**: REST route generation logic
- **GraphQL**: GraphQL schema generation
- **WebSocket**: WebSocket hook generation
- **Config**: YAML and class-based configuration loading

**Key Classes**:
- `RESTGenerator`: Generates REST routes from models
- `SchemaGenerator`: Generates GraphQL schemas
- `HookGenerator`: Generates WebSocket hooks
- `YAMLTableConfigLoader`: Loads and processes YAML configurations

**Dependencies**: Domain layer only

### Infrastructure Layer

**Location**: `src/infrastructure/`

**Purpose**: Provides adapters for external systems and services.

**Components**:
- **Database**: Connection management, reflection, migrations
- **Cache**: Redis caching implementation
- **Auth**: JWT and OAuth2 authentication
- **Config**: Configuration loading and validation

**Key Classes**:
- `DatabaseManager`: Manages database connections and sessions
- `DatabaseReflection`: Reflects database schemas
- `DefaultRedisCache`: Redis caching implementation
- `DefaultJWTAuthentication`: JWT authentication
- `DefaultOAuth2Authentication`: OAuth2 authentication
- `YAMLLoader`: Loads YAML configuration files

**Dependencies**: Domain layer

### Presentation Layer

**Location**: `src/presentation/`

**Purpose**: Handles HTTP requests, WebSocket connections, and API documentation.

**Components**:
- **REST**: REST endpoint handlers (GET, POST, PUT, DELETE)
- **GraphQL**: GraphQL query and mutation handlers
- **WebSocket**: WebSocket connection handlers
- **Docs**: OpenAPI/Swagger and GraphiQL interfaces
- **Middleware**: Authentication, CORS, caching middleware

**Key Classes**:
- `LightApi`: Main application class
- REST handlers: `GetHandler`, `PostHandler`, `PutHandler`, `DeleteHandler`
- `createGraphQLRoute`: GraphQL route factory
- `createWebSocketRoute`: WebSocket route factory
- `OpenAPIGenerator`: Generates OpenAPI specifications

**Dependencies**: Application and Infrastructure layers

## Data Flow

### Request Flow

1. **Request arrives** at Presentation layer (Starlette)
2. **Middleware processes** request (auth, CORS, caching)
3. **Route handler** (REST/GraphQL/WebSocket) processes request
4. **Application layer** orchestrates business logic
5. **Domain layer** validates and processes entities
6. **Infrastructure layer** interacts with database/cache
7. **Response flows back** through layers

### Model Registration Flow

1. **Developer defines model** inheriting from `RestEndpoint`
2. **Calls `app.register(model)`** on LightApi
3. **Application layer** generates routes:
   - REST routes via `RESTGenerator`
   - GraphQL schema via `SchemaGenerator`
   - WebSocket hooks via `HookGenerator`
4. **Presentation layer** registers routes with Starlette
5. **Endpoints are live** and accessible

## Key Design Principles

### Separation of Concerns

Each layer has a single, well-defined responsibility:
- **Domain**: Business rules and entities
- **Application**: Use cases and orchestration
- **Infrastructure**: External adapters
- **Presentation**: Request/response handling

### Dependency Direction

Dependencies flow downward only:
- Presentation → Application → Domain
- Infrastructure → Domain
- **Domain never depends on Infrastructure or Presentation**

### Extensibility

- **Plugins**: Extend functionality via plugin system
- **Custom Authentication**: Implement custom auth classes
- **Custom Caching**: Implement custom cache backends
- **Middleware**: Add custom middleware

## Component Relationships

### LightApi

The main application class that:
- Initializes all layers
- Manages model registration
- Coordinates endpoint generation
- Handles configuration

### RestEndpoint

Base class for all models that:
- Provides SQLAlchemy declarative base
- Defines configuration structure
- Enables automatic endpoint generation

### DatabaseManager

Manages database connections:
- Handles async/sync modes
- Manages connection pooling
- Provides session management

## Configuration Flow

1. **Configuration loaded** (YAML or class-based)
2. **Validated** by Infrastructure layer
3. **Applied** to LightApi instance
4. **Used** by Application layer for endpoint generation
5. **Respected** by Presentation layer for request handling

## Extension Points

### Custom Authentication

Extend `DefaultJWTAuthentication` or `DefaultOAuth2Authentication`:

```python
from src.infrastructure.auth.jwt import DefaultJWTAuthentication

class CustomAuth(DefaultJWTAuthentication):
    # Custom authentication logic
    pass
```

### Custom Caching

Extend `DefaultRedisCache`:

```python
from src.infrastructure.cache.redis import DefaultRedisCache

class CustomCache(DefaultRedisCache):
    # Custom caching logic
    pass
```

### Plugins

Implement the `Plugin` interface:

```python
from src.domain.plugins.interface import Plugin

class CustomPlugin(Plugin):
    def initialize(self, app):
        # Plugin initialization
        pass
    
    def register(self, app):
        # Register routes, middleware, etc.
        pass
```

## Next Steps

- Learn about [REST Endpoints](../building-apis/rest-endpoints.md)
- Explore [GraphQL](../building-apis/graphql.md)
- Understand [Configuration](../building-apis/yaml-configuration.md)
- Check out [Customization](../customization/index.md) options

