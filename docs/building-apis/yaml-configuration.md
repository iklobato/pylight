# YAML Configuration

Pylight supports YAML-based configuration for defining your entire API structure, including database connections, table configurations, authentication, permissions, and features.

## Overview

YAML configuration allows you to:

- **Define API Structure**: Configure all tables and endpoints in one file
- **Database Reflection**: Automatically generate models from existing databases
- **Feature Configuration**: Enable/disable and configure features per table
- **Authentication Setup**: Configure JWT/OAuth2 and permissions
- **Start from YAML**: Launch Pylight directly from a YAML file

## Basic Example

Minimal YAML configuration:

```yaml
database:
  url: "postgresql://postgres:postgres@localhost:5432/pylight"

swagger:
  title: "Pylight API"
  version: "1.0.0"

tables:
  - name: "products"
  - name: "users"
```

[View source: `docs/examples/yaml_configs/basic_config.yaml`](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/basic_config.yaml)

## Starting from YAML

Start Pylight with a YAML configuration:

```bash
pylight start --config config.yaml
```

Or programmatically:

```python
from pylight.presentation.app import LightApi

app = LightApi.fromYamlConfig("config.yaml")
app.run(host="localhost", port=8000)
```

## Configuration Structure

### Database Configuration

```yaml
database:
  url: "postgresql://user:password@host:port/database"
```

Supported databases:
- PostgreSQL: `postgresql://...`
- MySQL: `mysql://...`
- SQLite: `sqlite:///path/to/db.db`

**Note**: For async mode (default), PostgreSQL URLs are automatically converted to `postgresql+asyncpg://` format.

### Swagger Configuration

```yaml
swagger:
  title: "My API"
  version: "1.0.0"
  description: "API description"
```

### Table Configuration

```yaml
tables:
  - name: "products"
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
      caching:
        enabled: true
```

## Complete Configuration Example

```yaml
database:
  url: "postgresql://postgres:postgres@localhost:5432/pylight"

swagger:
  title: "Pylight API"
  version: "1.0.0"
  description: "Complete API configuration example"

authentication:
  jwt:
    secret_key: "your-secret-key"

tables:
  - name: "products"
    methods: ["GET", "POST", "PUT", "DELETE"]
    authentication:
      required: true
    permissions:
      GET: []
      POST: ["admin"]
      PUT: ["admin"]
      DELETE: ["admin"]
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

  - name: "users"
    methods: ["GET", "POST"]
    authentication:
      required: false
    features:
      pagination:
        enabled: true
```

[View source: `docs/examples/yaml_configs/features_config.yaml`](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/features_config.yaml)

## Feature Configuration

### Pagination

```yaml
features:
  pagination:
    enabled: true
    default_page_size: 20
    max_page_size: 200
```

### Filtering

```yaml
features:
  filtering:
    enabled: true
```

### Sorting

```yaml
features:
  sorting:
    enabled: true
```

### Caching

```yaml
features:
  caching:
    enabled: true
```

### GraphQL

```yaml
features:
  graphql: true  # or false
```

### WebSocket

```yaml
features:
  websocket: true  # or false
```

## Authentication Configuration

### JWT Authentication

```yaml
authentication:
  jwt:
    secret_key: "your-secret-key"

tables:
  - name: "products"
    authentication:
      required: true
    permissions:
      GET: []
      POST: ["admin"]
```

[View source: `docs/examples/yaml_configs/auth_config.yaml`](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/auth_config.yaml)

### OAuth2 Authentication

```yaml
authentication:
  oauth2:
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    authorization_url: "https://oauth-provider.com/authorize"
    token_url: "https://oauth-provider.com/token"
```

## Permissions

Configure role-based access control:

```yaml
tables:
  - name: "products"
    permissions:
      GET: []              # Any authenticated user
      POST: ["admin"]      # Only admin role
      PUT: ["admin", "editor"]  # Admin or editor
      DELETE: ["admin"]    # Only admin
```

## Method Restrictions

Limit which HTTP methods are available:

```yaml
tables:
  - name: "readonly_data"
    methods: ["GET"]  # Only GET, no POST/PUT/DELETE
```

## Validation

YAML configuration is validated on load:

- **Structure Validation**: Ensures required fields are present
- **Type Validation**: Validates field types
- **Value Validation**: Validates field values
- **Database Validation**: Verifies tables exist in database
- **Error Messages**: Detailed error messages with field paths and suggestions

Example error message:

```
Validation error in tables[0].features.pagination.default_page_size: 
field 'default_page_size' must be a positive integer, got str. 
Suggestion: Set a positive integer for default page size.
```

## Database Reflection

YAML configuration automatically reflects database schemas:

1. **Load YAML**: Configuration is loaded and validated
2. **Connect to Database**: Connection is established
3. **Reflect Tables**: Table schemas are reflected from database
4. **Generate Models**: Models are generated dynamically
5. **Register Endpoints**: Endpoints are registered with the app

## Best Practices

1. **Use Environment Variables**: Store sensitive data (secrets, passwords) in environment variables
2. **Version Control**: Keep YAML files in version control (excluding secrets)
3. **Validate Early**: Validate configuration before deployment
4. **Document Configuration**: Add comments to explain complex configurations
5. **Use Defaults**: Leverage default values to keep configuration minimal

## Troubleshooting

### Invalid YAML Syntax

Check YAML syntax:

```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### Database Connection Errors

Verify database URL format and credentials:

```yaml
database:
  url: "postgresql://user:password@host:port/database"
```

### Table Not Found

Ensure tables exist in database:

```bash
psql -U postgres -d pylight -c "\dt"
```

## Examples

For complete YAML configuration examples, see:
- [Basic Config](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/basic_config.yaml)
- [Features Config](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/features_config.yaml)
- [Auth Config](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/auth_config.yaml)

## Next Steps

- Learn about [Database Reflection](database-reflection.md) for existing databases
- Explore [Authentication](authentication.md) for security
- Check out [Use Cases](../use-cases/index.md) for real-world examples

