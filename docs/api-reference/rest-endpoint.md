# RestEndpoint

Base class for all REST endpoints/models in Pylight.

## Class Definition

```python
class RestEndpoint(Base):
    """Base class for all REST endpoints/models."""
```

## Configuration

### Nested Configuration Class

```python
class Configuration:
    """Endpoint-level configuration."""
    
    authentication_class: Optional[Type[Any]] = None
    required_roles: dict[str, list[str]] = {}
    caching_class: Optional[Type[Any]] = None
    caching_method_names: list[str] = []
    pagination_class: Optional[Type[Any]] = None
```

**Configuration Options**:
- `authentication_class`: Custom authentication class
- `required_roles`: Dictionary mapping HTTP method to list of required roles
- `caching_class`: Custom caching class
- `caching_method_names`: List of HTTP methods to cache
- `pagination_class`: Custom pagination class

## Class Methods

### `getConfiguration`

Get endpoint-level configuration instance.

```python
@classmethod
def getConfiguration(cls) -> Any
```

**Returns**:
- Configuration instance

### `getTableName`

Get the table name for this model.

```python
@classmethod
def getTableName(cls) -> str
```

**Returns**:
- Table name (from `__tablename__` or lowercase class name)

## Usage Example

```python
from pylight.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String
from pylight.infrastructure.auth.jwt import DefaultJWTAuthentication

class Product(RestEndpoint):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)
    
    class Configuration:
        authentication_class = DefaultJWTAuthentication
        required_roles = {
            "GET": [],
            "POST": ["admin"]
        }
        caching_method_names = ["GET"]
```

## Next Steps

- Learn about [LightApi](light-api.md) for app creation
- Explore [Configuration Options](configuration-options.md) for setup

