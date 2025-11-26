# Database Reflection

Pylight can automatically generate models from existing database schemas, eliminating the need to manually define models for existing databases.

## Overview

Database reflection allows you to:

- **Generate Models from Database**: Automatically create models from existing tables
- **No Manual Model Definition**: Skip writing model classes
- **YAML-Driven**: Configure everything via YAML
- **Schema Discovery**: Automatically discover table structures

## Basic Usage

### Using YAML Configuration

Simply specify table names in your YAML file:

```yaml
database:
  url: "postgresql://postgres:postgres@localhost:5432/pylight"

tables:
  - name: "products"
  - name: "users"
  - name: "orders"
```

Pylight will:
1. Connect to the database
2. Reflect the table schemas
3. Generate models dynamically
4. Register endpoints

### Programmatic Usage

```python
from pylight.infrastructure.database.reflection import DatabaseReflection
from pylight.presentation.app import LightApi

# Reflect database
reflection = DatabaseReflection("postgresql://postgres:postgres@localhost:5432/pylight")
table_info = reflection.reflectTable("products")

# Use reflected schema to generate models
# (Models are generated automatically when using YAML)
```

## How It Works

1. **Database Connection**: Pylight connects to your database
2. **Schema Reflection**: SQLAlchemy reflects table structures
3. **Model Generation**: Models are generated dynamically
4. **Endpoint Registration**: REST, GraphQL, and WebSocket endpoints are created

## Supported Databases

- **PostgreSQL**: Full support with async driver
- **MySQL**: Full support
- **SQLite**: Full support

## Table Discovery

Reflect all tables in a database:

```python
from pylight.infrastructure.database.reflection import DatabaseReflection

reflection = DatabaseReflection("postgresql://postgres:postgres@localhost:5432/pylight")
tables = reflection.reflectTables()
print(tables)  # ['products', 'users', 'orders']
```

## Column Types

Pylight automatically maps database column types to SQLAlchemy types:

- `INTEGER` → `Integer`
- `VARCHAR` → `String`
- `TEXT` → `Text`
- `BOOLEAN` → `Boolean`
- `TIMESTAMP` → `DateTime`
- `FLOAT` → `Float`
- `DECIMAL` → `Numeric`

## Relationships

Foreign key relationships are automatically discovered:

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id)
);
```

Pylight will reflect these relationships and make them available in GraphQL queries.

## Configuration with Reflection

Combine reflection with feature configuration:

```yaml
database:
  url: "postgresql://postgres:postgres@localhost:5432/pylight"

tables:
  - name: "products"
    methods: ["GET", "POST", "PUT", "DELETE"]
    features:
      pagination:
        enabled: true
      caching:
        enabled: true
```

## Validation

Pylight validates that:

- **Tables Exist**: All specified tables exist in the database
- **Connection Works**: Database connection is successful
- **Schema is Valid**: Table schemas can be reflected

Example error:

```
Tables not found in database: invalid_table. 
Available tables: products, users, orders. 
Action: Ensure table names in YAML match existing database tables.
```

## Limitations

- **Complex Relationships**: Very complex relationships may need manual model definition
- **Custom Types**: Custom database types may need manual mapping
- **Views**: Database views are not automatically reflected (use tables)

## Best Practices

1. **Use Existing Tables**: Reflection works best with existing, well-structured tables
2. **Validate Early**: Check table existence before deployment
3. **Combine with YAML**: Use YAML configuration for reflection + features
4. **Document Schema**: Keep database schema documentation up to date

## Troubleshooting

### Table Not Found

Ensure table names match exactly (case-sensitive for some databases):

```yaml
tables:
  - name: "products"  # Must match exact table name
```

### Connection Errors

Verify database URL and credentials:

```yaml
database:
  url: "postgresql://user:password@host:port/database"
```

### Schema Reflection Errors

Check table structure:

```sql
\d products  -- PostgreSQL
DESCRIBE products;  -- MySQL
```

## Examples

For complete reflection examples, see:
- [YAML Configuration](yaml-configuration.md) for YAML-based reflection
- [Use Cases](../use-cases/database-migration.md) for migration scenarios

## Next Steps

- Learn about [YAML Configuration](yaml-configuration.md) for complete setup
- Explore [REST Endpoints](rest-endpoints.md) for generated endpoints
- Check out [Use Cases](../use-cases/index.md) for real-world examples

