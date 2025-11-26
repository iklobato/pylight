# Configuration Options

Complete reference for all configuration options in Pylight.

## LightApi Configuration

### Constructor Parameters

- `databaseUrl` (Optional[str]): Database connection URL
- `swaggerTitle` (str): Swagger documentation title
- `swaggerVersion` (str): API version
- `swaggerDescription` (str): API description
- `configPath` (Optional[str]): Path to YAML configuration file
- `configClass` (Optional[Type[Any]]): Python class for configuration

## RestEndpoint Configuration

### Configuration Class Attributes

- `authentication_class` (Optional[Type[Any]]): Custom authentication class
- `required_roles` (dict[str, list[str]]): Dictionary mapping HTTP method to list of required roles
- `caching_class` (Optional[Type[Any]]): Custom caching class
- `caching_method_names` (list[str]): List of HTTP methods to cache
- `pagination_class` (Optional[Type[Any]]): Custom pagination class
- `websocket_class` (Optional[Type[WebSocketHandler]]): Custom WebSocket handler class

## YAML Configuration

### Database Configuration

```yaml
database:
  url: "postgresql://user:password@host:port/database"
```

### Swagger Configuration

```yaml
swagger:
  title: "API Title"
  version: "1.0.0"
  description: "API Description"
```

### Authentication Configuration

```yaml
authentication:
  jwt:
    secret_key: "secret-key"
  oauth2:
    client_id: "client-id"
    client_secret: "client-secret"
    authorization_url: "https://oauth-provider.com/authorize"
    token_url: "https://oauth-provider.com/token"
```

### Table Configuration

```yaml
tables:
  - name: "table_name"
    methods: ["GET", "POST", "PUT", "DELETE"]
    authentication:
      required: true
    permissions:
      GET: []
      POST: ["admin"]
    features:
      pagination:
        enabled: true
        default_page_size: 20
        max_page_size: 200
      filtering:
        enabled: true
      sorting:
        enabled: true
      caching:
        enabled: true
      graphql: true
      websocket: true
```

## Next Steps

- Learn about [YAML Configuration](../building-apis/yaml-configuration.md) for YAML setup
- Explore [RestEndpoint](rest-endpoint.md) for model configuration

