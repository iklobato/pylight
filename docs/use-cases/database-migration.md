# Database Migration

Complete example of generating models from an existing database using database reflection.

## Overview

This use case demonstrates:
- Connecting to existing database
- Reflecting table schemas
- Generating models automatically
- Using YAML configuration

## Step 1: Create YAML Configuration

```yaml
database:
  url: "postgresql://postgres:postgres@localhost:5432/pylight"

tables:
  - name: "products"
  - name: "users"
  - name: "orders"
```

[View source: `docs/examples/yaml_configs/basic_config.yaml`](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/basic_config.yaml)

## Step 2: Start Application

```python
from pylight.presentation.app import LightApi

app = LightApi.fromYamlConfig("config.yaml")
app.run(host="localhost", port=8000)
```

Pylight will:
1. Connect to database
2. Reflect table schemas
3. Generate models dynamically
4. Register endpoints

## Step 3: Verify Endpoints

All endpoints are automatically available:

- `GET /api/products`
- `GET /api/users`
- `GET /api/orders`

## Next Steps

- Learn about [Database Reflection](../building-apis/database-reflection.md) for details
- Explore [YAML Configuration](../building-apis/yaml-configuration.md) for configuration

