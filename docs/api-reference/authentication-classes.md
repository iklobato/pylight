# Authentication Classes

Documentation for authentication classes in Pylight.

## DefaultJWTAuthentication

Default JWT authentication implementation.

### Class Definition

```python
class DefaultJWTAuthentication(JWTAuthentication):
    """Default JWT authentication implementation with role support."""
```

### Methods

#### `authenticate`

Authenticate using JWT token from Authorization header.

```python
async def authenticate(self, request: Request) -> Optional[dict[str, Any]]
```

**Parameters**:
- `request` (Request): Starlette request object

**Returns**:
- `Optional[dict[str, Any]]`: User data dictionary with username and role if authenticated, None otherwise

**Raises**:
- `AuthenticationError`: If JWT token is invalid

## DefaultOAuth2Authentication

Default OAuth2 authentication implementation.

### Class Definition

```python
class DefaultOAuth2Authentication(OAuth2Authentication):
    """Default OAuth2 authentication implementation."""
```

### Constructor

```python
def __init__(
    self,
    clientId: str,
    clientSecret: str,
    authorizationUrl: str,
    tokenUrl: str
) -> None
```

**Parameters**:
- `clientId` (str): OAuth2 client ID
- `clientSecret` (str): OAuth2 client secret
- `authorizationUrl` (str): OAuth2 authorization URL
- `tokenUrl` (str): OAuth2 token URL

### Methods

#### `authenticate`

Authenticate using OAuth2.

```python
async def authenticate(self, request: Request) -> Optional[dict[str, Any]]
```

**Parameters**:
- `request` (Request): Starlette request object

**Returns**:
- `Optional[dict[str, Any]]`: User data dictionary if authenticated, None otherwise

**Raises**:
- `AuthenticationError`: If OAuth2 authentication fails

## Next Steps

- Learn about [Authentication](../building-apis/authentication.md) for usage
- Explore [Custom Authentication](../customization/custom-authentication.md) for customization

