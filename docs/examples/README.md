# Pylight Integration Examples

This directory contains integration example scripts that validate all Pylight framework features work correctly.

## Prerequisites

Before running the integration examples, ensure you have:

1. **PostgreSQL Docker Container Running**:
   ```bash
   docker run -d \
     --name pylight-postgres \
     -p 5432:5432 \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=pylight \
     postgres:latest
   ```

2. **Redis Running** (for caching examples):
   ```bash
   docker run -d \
     --name pylight-redis \
     -p 6379:6379 \
     redis:latest
   ```

3. **Python Dependencies Installed**:
   ```bash
   pip install -r requirements.txt
   # Or if using uv:
   uv pip install -e .
   ```

4. **Framework Code Available**: The Pylight framework code must be in the Python path (installed or PYTHONPATH set).

## Running Examples

Each example script is standalone and can be run independently:

### Basic Usage Example
```bash
cd docs/examples
python basic_usage.py
```

**What it tests**: 
- Basic framework setup
- Simple model registration
- Framework initialization

### REST Endpoints Example
```bash
cd docs/examples
python rest_endpoints.py
```

**What it tests**: 
- GET, POST, PUT, DELETE endpoints
- Database state validation
- Response structure validation

### GraphQL Example
```bash
python graphql_queries.py
```

**What it tests**:
- GraphQL queries and mutations
- Filtering
- Database consistency
- GraphiQL interface

### WebSocket Hooks Example
```bash
python websocket_hooks.py
```

**What it tests**:
- WebSocket connection establishment
- Real-time message delivery
- Multiple client subscriptions

### Basic Usage Example
```bash
python basic_usage.py
```

**What it tests**:
- Basic framework setup and configuration
- Simple model registration
- Framework initialization

### Comprehensive Integration Example
```bash
python comprehensive_integration.py
```

**What it tests**:
- All framework features in a single execution
- End-to-end functionality
- Database state persistence
- Feature interactions

**Expected Duration**: < 5 minutes

## Example Output

Successful example execution shows:

```
============================================================
REST Endpoints Validation Example
============================================================

1. Verifying dependencies...
   ✓ PostgreSQL connection verified

2. Starting server...
   ✓ Server started on http://127.0.0.1:8000

3. Testing POST /api/products...
   ✓ Product created with ID: 1

4. Validating database state after POST...
   ✓ Database state validated

...

✓ All REST endpoint tests passed!
============================================================
```

## Troubleshooting

### PostgreSQL Not Available
```
ERROR: PostgreSQL not available: connection refused
Please ensure PostgreSQL Docker container is running:
  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
```

**Solution**: Start the PostgreSQL container as shown in Prerequisites.

### Redis Not Available
```
ERROR: Redis not available: connection refused
Please ensure Redis is running:
  docker run -d -p 6379:6379 redis
```

**Solution**: Start the Redis container as shown in Prerequisites.

### Port Already in Use
```
ERROR: Port 8000 already in use
```

**Solution**: Either stop the process using port 8000, or modify the example script to use a different port.

### Database Connection Failed
```
ERROR: Could not connect to database
```

**Solution**: 
1. Verify PostgreSQL container is running: `docker ps`
2. Check connection string matches container configuration
3. Verify database `pylight` exists (or create it)

### Framework Import Errors
```
ModuleNotFoundError: No module named 'src'
```

**Solution**: 
1. Install framework in development mode: `pip install -e .`
2. Or set PYTHONPATH: `export PYTHONPATH=/path/to/pylight:$PYTHONPATH`

## File Structure

```
docs/examples/
├── README.md                    # This file
├── app_module.py                # Shared application module for examples
├── utils.py                     # Server management utilities
├── db_utils.py                  # Database utilities
├── test_models.py               # Test models (Product, User)
├── test_config.yaml             # Test configuration
├── test_config_class.py         # Test configuration class
├── basic_usage.py                # Basic usage example
├── comprehensive_integration.py  # Comprehensive example (all features)
├── rest_endpoints.py             # REST endpoints example
├── graphql_queries.py           # GraphQL example
└── websocket_hooks.py            # WebSocket example
```

## Example Script Structure

Each example script follows this pattern:

```python
#!/usr/bin/env python3
"""Example: Feature Validation"""

import sys
import os
import requests

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from docs.examples.utils import verify_postgres, start_server, wait_for_server, stop_server
from docs.examples.db_utils import create_database_connection, cleanup_test_data

def main():
    # 1. Verify dependencies
    # 2. Start server
    # 3. Run tests
    # 4. Validate database state
    # 5. Cleanup

if __name__ == "__main__":
    main()
```

## Next Steps

After running examples successfully:

1. Review example code to understand framework usage patterns
2. Use examples as templates for your own integration tests
3. Extend examples to test additional scenarios
4. Report any failures or unexpected behavior

## Additional Resources

- Framework Documentation: `docs/api/README.md`
- Framework Source: `src/`
- Main Framework Spec: `specs/001-pylight-framework/spec.md`

