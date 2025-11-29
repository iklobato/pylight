# External Database Integration Tests

This directory contains comprehensive integration tests for validating Pylight functionality with external PostgreSQL databases.

## Overview

These tests validate that Pylight works correctly with external databases, covering:
- REST CRUD operations
- Advanced query features (pagination, filtering, sorting)
- GraphQL queries and mutations
- YAML configuration loading
- Database schema reflection
- CLI tools
- Redis caching (optional)
- Helm chart deployment (manual procedures)
- WebSocket real-time features (manual procedures)
- Authentication and authorization (manual procedures)

## Directory Structure

```
tests/external-db/
├── __init__.py
├── conftest.py                 # Pytest configuration and shared fixtures
├── setup/                      # Database setup and teardown
│   ├── database_docker.py      # Docker database deployment
│   ├── database_kubernetes.py  # Kubernetes in-cluster database deployment
│   ├── schema_generator.py     # Database schema generation
│   └── data_generator.py       # Test data generation using Faker
├── automated/                  # Automated test scripts
│   ├── test_rest_crud.py       # REST CRUD operations
│   ├── test_pagination.py      # Pagination tests
│   ├── test_filtering.py       # Filtering tests
│   ├── test_sorting.py         # Sorting tests
│   ├── test_graphql.py         # GraphQL queries and mutations
│   ├── test_yaml_config.py     # YAML configuration loading
│   ├── test_reflection.py      # Database reflection
│   ├── test_cli.py             # CLI tools
│   └── test_caching.py         # Redis caching
├── manual/                     # Manual test procedures
│   ├── websocket_procedures.md # WebSocket testing steps
│   ├── auth_procedures.md      # Authentication testing steps
│   └── helm_procedures.md      # Helm chart deployment testing steps
├── fixtures/                   # Test fixtures and utilities
│   ├── api_client.py           # HTTP client utilities
│   ├── database_client.py      # Database connection utilities
│   ├── test_data.py            # Test data definitions
│   └── test_config.yaml        # Example YAML configuration
└── reports/                    # Test result reports (generated)
    └── .gitignore              # Ignore generated reports
```

## Prerequisites

1. **Python 3.11+**
2. **PostgreSQL 15+** (accessible via Docker or Kubernetes)
3. **Pylight API** running and accessible
4. **Test dependencies** installed:
   ```bash
   pip install -r requirements-test.txt
   ```

## Quick Start

### 1. Setup Database

**Docker (Local Testing)**:
```bash
./scripts/external-db-test/setup_database.sh --docker
```

**Kubernetes (Helm Testing)**:
```bash
./scripts/external-db-test/setup_database.sh --kubernetes --namespace test-db
```

### 2. Generate Test Data

```bash
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/pylight_test"
python3 scripts/external-db-test/generate_test_data.py
```

### 3. Run Automated Tests

```bash
export PYLIGHT_BASE_URL="http://localhost:8000"
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/pylight_test"
./scripts/external-db-test/run_automated_tests.sh
```

### 4. Run Manual Tests

See individual procedure files in `manual/` directory:
- `helm_procedures.md` - Helm chart deployment testing
- `websocket_procedures.md` - WebSocket testing
- `auth_procedures.md` - Authentication testing

## Test Data

The test suite uses a production-like e-commerce schema with 10+ tables:
- **Users**: 1000+ users with various roles
- **Products**: 1000+ products across categories
- **Categories**: 50+ categories with hierarchy
- **Orders**: 2000+ orders with various statuses
- **OrderItems**: 5000+ order items
- **Addresses**: 2000+ addresses
- **Reviews**: 3000+ reviews
- **Payments**: 2000+ payments
- **Shipments**: 2000+ shipments
- **Inventory**: 1000+ inventory records

Total: **10,000+ records** across all tables.

## Configuration

Tests use environment variables for configuration:

- `TEST_DATABASE_URL`: PostgreSQL connection string
- `PYLIGHT_BASE_URL`: Pylight API base URL (default: http://localhost:8000)
- `TEST_DATA_SEED`: Random seed for reproducible test data (default: 42)
- `RECORDS_PER_TABLE`: Number of records per table (default: 1000)
- `REDIS_ENABLED`: Enable Redis caching tests (default: false)

## Running Specific Tests

```bash
# Run only REST CRUD tests
pytest tests/external-db/automated/test_rest_crud.py

# Run only pagination tests
pytest tests/external-db/automated/test_pagination.py

# Run all automated tests
pytest tests/external-db/automated/ -m automated

# Run with verbose output
pytest tests/external-db/automated/ -v
```

## Test Reports

Test reports are generated in `tests/external-db/reports/`:
- `test-report.html` - HTML test report
- `test-report.json` - JSON test report
- `test-report.xml` - JUnit XML report (for CI/CD)

## Cleanup

```bash
# Cleanup Docker database
./scripts/external-db-test/cleanup.sh --docker

# Cleanup Kubernetes database
./scripts/external-db-test/cleanup.sh --kubernetes --namespace test-db
```

## Troubleshooting

### Pylight API Not Running

**Symptoms**: Tests fail with "Pylight API is not ready" or connection errors.

**Solutions**:
1. **Start Pylight manually**:
   ```bash
   export PYTHONPATH=/Users/iklo/pylight:$PYTHONPATH
   ./scripts/external_db_test/start_pylight.sh
   ```

2. **Use auto-start** (recommended for CI):
   ```bash
   ./scripts/external_db_test/run_automated_tests.sh --auto-start
   ```

3. **Check if Pylight is already running**:
   ```bash
   curl http://localhost:8000/health
   ```

4. **Check Pylight logs**:
   ```bash
   tail -50 tests/external_db/reports/pylight.stderr.log
   tail -50 tests/external_db/reports/pylight.stdout.log
   ```

5. **Verify config file**:
   ```bash
   cat tests/external_db/fixtures/test_config.yaml
   ```

### Database Connection Errors

**Symptoms**: "connection refused", "database does not exist", or connection timeouts.

**Solutions**:
- Verify database is running and accessible:
  ```bash
  psql -h localhost -U postgres -d pylight_test -c "SELECT 1;"
  ```
- Check connection string format: `postgresql://user:password@host:port/database`
- Verify network connectivity (for Kubernetes)
- Check database logs for errors

### Test Failures

**Symptoms**: Tests fail with assertion errors or API errors.

**Solutions**:
- **Check Pylight API is running**: `curl http://localhost:8000/health`
- **Verify test data has been generated**:
  ```bash
  python3 -c "
  from tests.external_db.fixtures.database_client import DatabaseClient
  client = DatabaseClient('postgresql://postgres:postgres@localhost:5432/pylight_test')
  client.connect()
  print('Products:', client.get_table_count('products'))
  client.close()
  "
  ```
- **Check database schema matches expected structure**
- **Review test logs for detailed error messages**:
  ```bash
  tail -100 tests/external_db/reports/test-execution.log
  ```

### Common Error Messages

**"Pylight API is not ready"**:
- Start Pylight: `./scripts/external_db_test/start_pylight.sh`
- Or use auto-start: `./scripts/external_db_test/run_automated_tests.sh --auto-start`

**"Chart.yaml file is missing"** (Helm tests):
- This is a known Helm 3.14.3 issue. Use the temporary directory workaround in test scripts.

**"Database reflection error"**:
- Verify database tables exist
- Check database connection string in config
- Ensure Pylight has permissions to access database

**"Connection refused"**:
- Verify Pylight is running: `curl http://localhost:8000/health`
- Check if port 8000 is in use: `lsof -i :8000`
- Review Pylight startup logs

### Performance Issues

- Reduce `RECORDS_PER_TABLE` for faster test execution:
  ```bash
  python3 scripts/external_db_test/generate_test_data.py --records-per-table 50
  ```
- Use smaller test datasets for development
- Run tests in parallel (if supported): `pytest -n auto`

### Log Files

All logs are stored in `tests/external_db/reports/`:

- **Pylight logs**:
  - `pylight.stdout.log` - Standard output
  - `pylight.stderr.log` - Standard error (most important for debugging)
  - `pylight.log` - Combined logs (if available)
  - `pylight.pid` - Process ID file

- **Test logs**:
  - `test-execution.log` - Full pytest output
  - `test-report.html` - HTML test report
  - `test-report.json` - JSON test report
  - `test-report.xml` - JUnit XML report

**View logs**:
```bash
# Pylight errors
tail -50 tests/external_db/reports/pylight.stderr.log

# Test execution
tail -50 tests/external_db/reports/test-execution.log

# Follow logs in real-time
tail -f tests/external_db/reports/pylight.stderr.log
```

### Manual Pylight Startup

If auto-start doesn't work, start Pylight manually:

```bash
export PYTHONPATH=/Users/iklo/pylight:$PYTHONPATH
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/pylight_test"

# Start Pylight
python3 -m cli start \
  --config tests/external_db/fixtures/test_config.yaml \
  --host 0.0.0.0 \
  --port 8000

# In another terminal, run tests
export PYLIGHT_BASE_URL="http://localhost:8000"
./scripts/external_db_test/run_automated_tests.sh
```

### Stopping Pylight

If Pylight was started by the test scripts:

```bash
# Using PID file
kill $(cat tests/external_db/reports/pylight.pid)

# Or manually find and kill
ps aux | grep "cli start"
kill <PID>
```

Or use the stop script (if created):
```bash
./scripts/external_db_test/stop_pylight.sh
```

## Contributing

When adding new tests:
1. Follow existing test structure and naming conventions
2. Use fixtures from `conftest.py` for common setup
3. Add appropriate pytest markers (`@pytest.mark.automated`)
4. Update this README if adding new test categories
5. Ensure tests are idempotent and can run multiple times

