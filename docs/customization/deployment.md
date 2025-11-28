# Deployment

This guide covers production deployment best practices for Pylight applications.

## Overview

Production deployment considerations:

- **Server Configuration**: Uvicorn and ASGI server setup
- **Environment Variables**: Secure configuration management
- **Database Setup**: Production database configuration
- **Security**: Security best practices
- **Monitoring**: Logging and monitoring setup

## Server Configuration

### Uvicorn Production Settings

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Multiple workers for production
        log_level="info"
    )
```

### Using Gunicorn with Uvicorn Workers

```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Environment Variables

### Configuration via Environment

```python
import os

app = LightApi(
    databaseUrl=os.getenv("DATABASE_URL"),
    swaggerTitle=os.getenv("API_TITLE", "Pylight API")
)
```

### .env File

```bash
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

## Database Setup

### PostgreSQL Production

```yaml
database:
  url: "postgresql://user:password@host:port/database"
```

### Connection Pooling

Configure connection pooling for production:

```python
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

## Security

### HTTPS

Always use HTTPS in production:

```python
# Use reverse proxy (nginx, traefik) for HTTPS
# Or use uvicorn with SSL certificates
uvicorn.run(app, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
```

### Secret Management

Store secrets securely:

- Use environment variables
- Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- Never commit secrets to version control

### CORS Configuration

Configure CORS properly:

```python
from starlette.middleware.cors import CORSMiddleware

app.starletteApp.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
```

## Monitoring

### Logging

Configure production logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Health Checks

Add health check endpoint:

```python
@app.route("/health")
async def health():
    return {"status": "healthy"}
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Kubernetes Deployment

Pylight can be deployed to Kubernetes using the provided Helm chart. See the [Helm Chart documentation](../../charts/pylight/README.md) for complete instructions.

### Quick Start

```bash
# Add Helm repository
helm repo add iklobato https://iklobato.github.io/pylight/charts
helm repo update

# Install
helm install my-api iklobato/pylight -f values.yaml
```

### Local Development

For local testing with minikube, see the [Local Development guide](../../charts/pylight/README.md#local-development) in the Helm chart documentation.

## Best Practices

1. **Use Environment Variables**: Never hardcode secrets
2. **Enable HTTPS**: Always use HTTPS in production
3. **Monitor Performance**: Set up monitoring and alerting
4. **Backup Database**: Regular database backups
5. **Test Deployments**: Test in staging before production

## Next Steps

- Learn about [Error Handling](error-handling.md)
- Explore [Troubleshooting](../troubleshooting/index.md) for common issues

