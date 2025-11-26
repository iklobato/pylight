# Authenticated API

Complete example of creating an authenticated API with JWT authentication and role-based access control.

## Overview

This use case demonstrates:
- JWT authentication setup
- Role-based access control
- Protected endpoints
- Token generation and validation

## Step 1: Configure Authentication

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
      PUT: ["admin"]
      DELETE: ["admin"]
```

[View source: `docs/examples/yaml_configs/auth_config.yaml`](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/auth_config.yaml)

## Step 2: Start Application

```python
from pylight.presentation.app import LightApi

app = LightApi.fromYamlConfig("config.yaml")
app.run(host="localhost", port=8000)
```

## Step 3: Generate JWT Token

```python
import jwt
import datetime

secret_key = "your-secret-key"
payload = {
    "username": "admin",
    "role": "admin",
    "sub": "admin",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
}
token = jwt.encode(payload, secret_key, algorithm="HS256")
print(f"Bearer {token}")
```

## Testing

### Authenticated Request

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/products
```

### Unauthenticated Request

```bash
curl http://localhost:8000/api/products
# Returns 401 Unauthorized
```

## Next Steps

- Learn about [Authentication](../building-apis/authentication.md) for details
- Explore [Custom Authentication](../customization/custom-authentication.md) for customization

