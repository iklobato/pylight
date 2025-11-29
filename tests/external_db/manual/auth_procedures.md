# Authentication and Authorization Test Procedures

This document provides step-by-step procedures for testing JWT and OAuth2 authentication with external databases.

## Prerequisites

- Pylight API running with authentication enabled
- External database with user data
- JWT secret key configured
- OAuth2 provider configured (if testing OAuth2)

## Step 1: Configure JWT Authentication

1. **Update Pylight configuration** to enable JWT:
```yaml
# config.yaml
authentication:
  jwt:
    enabled: true
    secret_key: "your-secret-key-here"
    algorithm: "HS256"
    expiration: 3600  # 1 hour
```

2. **Restart Pylight** to apply configuration

3. **Verify authentication is enabled**:
```bash
curl http://localhost:8000/api/products
# Should return 401 Unauthorized if endpoint requires auth
```

## Step 2: Generate JWT Token

### Option A: Using Pylight Auth Endpoint

```bash
# Login endpoint (if available)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password"}'

# Response should contain JWT token
```

### Option B: Generate Token Manually

```python
import jwt
import datetime

payload = {
    "user_id": 1,
    "username": "testuser",
    "role": "user",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}

token = jwt.encode(payload, "your-secret-key-here", algorithm="HS256")
print(f"JWT Token: {token}")
```

## Step 3: Test Protected Endpoints

1. **Access protected endpoint without token**:
```bash
curl http://localhost:8000/api/products
# Should return 401 Unauthorized
```

2. **Access protected endpoint with valid token**:
```bash
curl http://localhost:8000/api/products \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
# Should return 200 OK with data
```

3. **Access protected endpoint with invalid token**:
```bash
curl http://localhost:8000/api/products \
  -H "Authorization: Bearer invalid_token"
# Should return 401 Unauthorized
```

4. **Access protected endpoint with expired token**:
```bash
# Use token that has expired
curl http://localhost:8000/api/products \
  -H "Authorization: Bearer EXPIRED_TOKEN"
# Should return 401 Unauthorized
```

## Step 4: Test Role-Based Access Control

1. **Create token with user role**:
```python
payload = {
    "user_id": 1,
    "username": "testuser",
    "role": "user",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}
token_user = jwt.encode(payload, "secret", algorithm="HS256")
```

2. **Create token with admin role**:
```python
payload = {
    "user_id": 2,
    "username": "admin",
    "role": "admin",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}
token_admin = jwt.encode(payload, "secret", algorithm="HS256")
```

3. **Test user role access**:
```bash
# Access user-only endpoint
curl http://localhost:8000/api/products \
  -H "Authorization: Bearer USER_TOKEN"
# Should work if endpoint allows user role
```

4. **Test admin role access**:
```bash
# Access admin-only endpoint
curl http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
# Should work for admin role
```

5. **Test insufficient permissions**:
```bash
# User trying to access admin endpoint
curl http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer USER_TOKEN"
# Should return 403 Forbidden
```

## Step 5: Test OAuth2 Flow

1. **Initiate OAuth2 authorization**:
```bash
# Redirect to OAuth2 provider
open "http://localhost:8000/auth/oauth2/authorize?client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&response_type=code&scope=read"
```

2. **Complete OAuth2 login** on provider's page

3. **Receive authorization code** in redirect URI

4. **Exchange code for token**:
```bash
curl -X POST http://localhost:8000/auth/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=AUTHORIZATION_CODE&redirect_uri=REDIRECT_URI&client_id=CLIENT_ID&client_secret=CLIENT_SECRET"
```

5. **Use OAuth2 token** to access protected endpoints:
```bash
curl http://localhost:8000/api/products \
  -H "Authorization: Bearer OAUTH2_TOKEN"
```

## Step 6: Verify Database Integration

1. **Check user data in database**:
```sql
SELECT id, username, role FROM users WHERE username = 'testuser';
```

2. **Verify token claims match database**:
   - User ID in token should match database user ID
   - Role in token should match database user role

3. **Test token refresh** (if supported):
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Authorization: Bearer EXPIRING_TOKEN"
# Should return new token
```

## Troubleshooting

### 401 Unauthorized on All Requests

- Verify JWT secret key is correct
- Check token expiration time
- Verify token format is correct (Bearer token)

### 403 Forbidden on Admin Endpoints

- Verify user role in token matches required role
- Check role-based access control configuration
- Verify user role in database matches token

### OAuth2 Flow Fails

- Verify OAuth2 provider is configured correctly
- Check client_id and client_secret
- Verify redirect_uri matches provider configuration
- Check OAuth2 provider is accessible

