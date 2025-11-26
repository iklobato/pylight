# Installation

This guide covers installing Pylight and verifying the installation works correctly.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation Methods

### Using pip

```bash
pip install pylight
```

### Using uv (Recommended)

If you're using `uv` for Python package management:

```bash
uv pip install pylight
```

### From Source

To install from the GitHub repository:

```bash
git clone https://github.com/iklobato/pylight.git
cd pylight
pip install -e .
```

## Verify Installation

After installation, verify that Pylight is installed correctly:

```bash
# Check if pylight command is available
pylight --version

# Or verify Python import
python3 -c "from pylight.presentation.app import LightApi; print('Pylight installed successfully')"
```

## Dependencies

Pylight automatically installs the following dependencies:

- **Starlette** - ASGI web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - Database ORM
- **Strawberry GraphQL** - GraphQL support
- **PyJWT** - JWT authentication
- **python-jose** - JWT/OAuth2 utilities
- **redis** - Redis client for caching
- **PyYAML** - YAML configuration support
- **Alembic** - Database migrations
- **Click** - CLI framework
- **asyncpg** - Async PostgreSQL driver

## Database Setup

Pylight works with any SQLAlchemy-compatible database. For getting started, SQLite requires no additional setup:

```python
# SQLite (no setup required)
databaseUrl = "sqlite:///app.db"
```

For PostgreSQL or MySQL, you'll need the database server running and connection credentials:

```python
# PostgreSQL
databaseUrl = "postgresql://user:password@localhost:5432/dbname"

# MySQL
databaseUrl = "mysql://user:password@localhost:3306/dbname"
```

## Optional: Redis for Caching

If you want to use Redis caching (optional), install and start Redis:

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally
# macOS: brew install redis
# Linux: apt-get install redis-server
```

## Troubleshooting

### Import Errors

If you encounter import errors, make sure Pylight is installed in the correct Python environment:

```bash
# Check which Python is being used
which python3

# Verify installation
pip list | grep pylight
```

### Database Connection Issues

If you have database connection issues:
- Verify your database server is running
- Check connection URL format
- Ensure database credentials are correct
- For PostgreSQL, ensure `asyncpg` is installed: `pip install asyncpg`

## Next Steps

Once Pylight is installed, proceed to the [Quick Start Guide](quick-start.md) to create your first API.

