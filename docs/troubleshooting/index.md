# Troubleshooting

Common issues and solutions when using Pylight.

## Common Issues

### Database Connection Errors

**Problem**: Cannot connect to database

**Solutions**:
- Verify database URL format
- Check database credentials
- Ensure database server is running
- For PostgreSQL, ensure `asyncpg` is installed

### Import Errors

**Problem**: Import errors when using Pylight

**Solutions**:
- Verify Pylight is installed: `pip install pylight`
- Check Python version (requires 3.11+)
- Verify virtual environment is activated

### Authentication Errors

**Problem**: 401 Unauthorized errors

**Solutions**:
- Verify JWT token is valid
- Check token expiration
- Ensure Authorization header format: `Bearer TOKEN`
- Verify secret key matches

### YAML Configuration Errors

**Problem**: YAML configuration validation errors

**Solutions**:
- Check YAML syntax
- Verify required fields are present
- Check field types match expected types
- Review error messages for specific field paths

### Table Not Found

**Problem**: Tables not found in database

**Solutions**:
- Verify table names match exactly (case-sensitive)
- Ensure tables exist in database
- Check database connection URL points to correct database

## Getting Help

- Check [Documentation](../index.md) for detailed guides
- Review [Examples](https://github.com/iklobato/pylight/tree/main/docs/examples) for code samples
- Open an issue on [GitHub](https://github.com/iklobato/pylight/issues)

## Next Steps

- Review [Getting Started](../getting-started/index.md) for setup
- Check [Use Cases](../use-cases/index.md) for examples

