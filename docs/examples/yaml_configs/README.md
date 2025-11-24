# YAML Configuration Examples

This directory contains example YAML configuration files demonstrating different ways to configure Pylight API endpoints.

## Example Files

### basic_config.yaml

**Purpose**: Minimal configuration example showing the simplest way to expose database tables as REST API endpoints.

**Features Demonstrated**:
- Basic database connection
- Table exposure with default settings
- All HTTP methods enabled by default
- All features enabled by default

**Use Case**: Quick start for developers who want to expose tables with minimal configuration.

**Usage**:
```bash
./scripts/test_yaml_config.sh docs/examples/yaml_configs/basic_config.yaml
```

---

### auth_config.yaml

**Purpose**: Demonstrates JWT authentication configuration and role-based access control.

**Features Demonstrated**:
- Global JWT authentication provider configuration
- Per-table authentication requirements
- Method-specific role permissions
- Public vs. authenticated endpoints

**Use Case**: APIs that require user authentication and need to restrict access based on user roles.

**Usage**:
```bash
./scripts/test_yaml_config.sh docs/examples/yaml_configs/auth_config.yaml
```

**Prerequisites**:
- JWT secret key configured (change `secret_key` in YAML for production)
- Users with JWT tokens containing `role` claim

---

### permissions_config.yaml

**Purpose**: Shows fine-grained permission configuration with different roles per HTTP method.

**Features Demonstrated**:
- Table-level role requirements
- Method-specific permissions (GET, POST, PUT, DELETE)
- Public access configuration
- Admin-only endpoints

**Use Case**: Complex permission scenarios where different user roles need different levels of access.

**Usage**:
```bash
./scripts/test_yaml_config.sh docs/examples/yaml_configs/permissions_config.yaml
```

**Prerequisites**:
- JWT authentication configured
- Users with appropriate roles (admin, user, etc.)

---

### features_config.yaml

**Purpose**: Demonstrates per-table feature configuration (caching, pagination, filtering, sorting, GraphQL, WebSocket).

**Features Demonstrated**:
- Caching configuration (requires Redis)
- Custom pagination settings (page size, max page size)
- Filtering enable/disable
- Sorting enable/disable
- GraphQL endpoint availability
- WebSocket endpoint availability

**Use Case**: Optimizing API performance and features per table based on usage patterns.

**Usage**:
```bash
./scripts/test_yaml_config.sh docs/examples/yaml_configs/features_config.yaml
```

**Prerequisites**:
- Redis running (for caching examples)
- Tables with appropriate data for testing pagination/filtering/sorting

---

## Common Configuration Patterns

### Minimal Configuration

```yaml
database:
  url: "postgresql://user:pass@localhost:5432/dbname"

tables:
  - name: "table_name"
```

### Authentication Required

```yaml
authentication:
  jwt:
    secret_key: "your-secret-key"

tables:
  - name: "protected_table"
    authentication:
      required: true
```

### Method-Specific Permissions

```yaml
tables:
  - name: "table_name"
    permissions:
      GET: []           # Any authenticated user
      POST: ["admin"]    # Only admins
      PUT: ["admin"]
      DELETE: ["admin"]
```

### Custom Pagination

```yaml
tables:
  - name: "table_name"
    features:
      pagination:
        enabled: true
        default_page_size: 20
        max_page_size: 100
```

### Disable Features

```yaml
tables:
  - name: "table_name"
    features:
      filtering:
        enabled: false
      sorting:
        enabled: false
      graphql: false
      websocket: false
```

---

## Testing Examples

### Start Server with Basic Config

```bash
./scripts/test_yaml_config.sh docs/examples/yaml_configs/basic_config.yaml
```

### Start Server on Custom Port

```bash
./scripts/test_yaml_config.sh docs/examples/yaml_configs/basic_config.yaml --port 8001
```

### Start Server with Authentication Config

```bash
./scripts/test_yaml_config.sh docs/examples/yaml_configs/auth_config.yaml
```

---

## Prerequisites

Before using these examples, ensure:

1. **PostgreSQL Docker container running**:
   ```bash
   docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:latest
   ```

2. **Redis Docker container running** (for caching examples):
   ```bash
   docker run -d --name redis -p 6379:6379 redis:latest
   ```

3. **Test database and tables created**:
   ```bash
   psql -h localhost -U postgres -c "CREATE DATABASE pylight;"
   # Then create tables as needed for your examples
   ```

4. **Pylight framework installed**:
   ```bash
   uv sync
   ```

---

## Notes

- All example files use `localhost:5432` for PostgreSQL - adjust if your setup differs
- JWT secret keys in examples are placeholders - change them for production use
- Example tables (products, users, orders) should exist in your test database
- Redis is optional but required for caching examples to work fully
- Each example file is self-contained and can be used independently

