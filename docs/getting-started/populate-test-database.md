# Populate Test Database

The `populate-test-database` command generates realistic test data for comprehensive Pylight feature testing.

## Quick Start

```bash
# Start PostgreSQL (Docker)
docker run -d \
  --name pylight-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=pylight_test \
  postgres:15

# Populate database
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/pylight_test"
pylight populate-test-database --create-schema
```

## Usage

### Basic Usage

```bash
pylight populate-test-database --create-schema
```

This creates the e-commerce schema (10+ tables) and populates each table with 1000 records.

### Custom Record Counts

```bash
pylight populate-test-database \
  --create-schema \
  --records-per-table 5000 \
  --table-counts '{"users": 2000, "products": 10000}'
```

### Reproducible Data

```bash
pylight populate-test-database \
  --create-schema \
  --seed 42
```

Using the same seed produces identical data across runs.

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--connection-string`, `-c` | PostgreSQL connection string | `$DATABASE_URL` |
| `--create-schema`, `-s` | Create/drop schema before populating | `False` |
| `--seed`, `-S` | Seed value for reproducibility | `None` |
| `--records-per-table`, `-r` | Default records per table | `1000` |
| `--table-counts`, `-t` | JSON dict of table counts | `{}` |
| `--cleanup-on-failure`, `-C` | Clean up partial data on failure | `True` |
| `--verbose`, `-v` | Enable verbose output | `False` |
| `--quiet`, `-q` | Suppress non-error output | `False` |

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `PYLIGHT_POPULATE_SEED`: Seed value for reproducibility
- `PYLIGHT_POPULATE_VERBOSE`: Enable verbose output

## Generated Schema

The command creates an e-commerce schema with 10+ interconnected tables:

- **users**: User accounts
- **categories**: Product categories (with parent-child relationships)
- **products**: Products with JSON dimensions
- **addresses**: User addresses
- **orders**: Customer orders
- **order_items**: Order line items
- **reviews**: Product reviews
- **payments**: Payment transactions
- **shipments**: Shipping information
- **inventory**: Product inventory

## Use with Pylight

After populating the database, use it with Pylight:

```bash
# Create YAML config
cat > config.yaml << EOF
database:
  url: "postgresql://postgres:postgres@localhost:5432/pylight_test"

tables:
  - name: "users"
  - name: "products"
  - name: "orders"
EOF

# Start Pylight
pylight start --config config.yaml
```

## See Also

- [Quick Start Guide](../specs/001-populate-test-database/quickstart.md)
- [CLI Contract](../specs/001-populate-test-database/contracts/cli-contract.md)
- [Example Configuration](../examples/populate-test-database-config.yaml)

