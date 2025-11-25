# Pagination, Filtering, and Sorting

Pylight provides built-in pagination, filtering, and sorting for list endpoints, making it easy to handle large datasets efficiently.

## Overview

Pylight automatically provides:

- **Pagination**: Page-based navigation with configurable page sizes
- **Filtering**: Query-based filtering with multiple operators
- **Sorting**: Single or multi-field sorting (ascending/descending)

All features work together seamlessly.

## Pagination

### Basic Usage

```bash
GET /api/products?page=1&limit=10
```

Response:

```json
{
  "items": [
    {"id": 1, "name": "Product 1"},
    {"id": 2, "name": "Product 2"}
  ],
  "total": 100,
  "page": 1,
  "limit": 10,
  "pages": 10
}
```

### Configuration

Configure pagination in YAML:

```yaml
tables:
  - name: "products"
    features:
      pagination:
        enabled: true
        default_page_size: 20
        max_page_size: 200
```

[View source: `docs/examples/yaml_configs/features_config.yaml`](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/features_config.yaml)

### Query Parameters

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: configured max_page_size)

### Response Fields

- `items`: Array of items for current page
- `total`: Total number of items
- `page`: Current page number
- `limit`: Items per page
- `pages`: Total number of pages

## Filtering

### Basic Filtering

Filter by field value:

```bash
GET /api/products?price__gt=100
GET /api/products?name__eq=Laptop
GET /api/products?status__in=active,pending
```

### Filter Operators

- `__eq`: Equals (`price__eq=100`)
- `__ne`: Not equals (`status__ne=deleted`)
- `__gt`: Greater than (`price__gt=100`)
- `__gte`: Greater than or equal (`price__gte=100`)
- `__lt`: Less than (`price__lt=1000`)
- `__lte`: Less than or equal (`price__lte=1000`)
- `__like`: Pattern matching (`name__like=laptop%`)
- `__in`: Value in list (`status__in=active,pending`)

### Multiple Filters

Combine multiple filters:

```bash
GET /api/products?price__gte=50&price__lte=200&status__eq=active
```

### Configuration

Enable/disable filtering:

```yaml
tables:
  - name: "products"
    features:
      filtering:
        enabled: true
```

## Sorting

### Basic Sorting

Sort by field:

```bash
GET /api/products?sort=price
GET /api/products?sort=-price  # Descending
```

### Multiple Fields

Sort by multiple fields:

```bash
GET /api/products?sort=category,price
GET /api/products?sort=category,-price  # Category ascending, price descending
```

### Configuration

Enable/disable sorting:

```yaml
tables:
  - name: "products"
    features:
      sorting:
        enabled: true
```

## Combined Usage

Combine pagination, filtering, and sorting:

```bash
GET /api/products?page=2&limit=20&price__gte=100&sort=-price
```

This query:
- Gets page 2
- 20 items per page
- Filters products with price >= 100
- Sorts by price descending

## GraphQL Support

All features work with GraphQL:

```graphql
query {
  products(
    page: 1
    limit: 10
    filter: {price: {gte: 100}}
    sort: "-price"
  ) {
    id
    name
    price
  }
}
```

## Performance Considerations

### Indexing

Ensure database indexes on frequently filtered/sorted fields:

```sql
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_status ON products(status);
```

### Large Datasets

For very large datasets:
- Use appropriate page sizes
- Index filtered/sorted columns
- Consider cursor-based pagination for very large datasets

## Configuration Examples

### High-Traffic Table

```yaml
tables:
  - name: "products"
    features:
      pagination:
        enabled: true
        default_page_size: 20
        max_page_size: 200
      filtering:
        enabled: true
      sorting:
        enabled: true
```

### Read-Only Table

```yaml
tables:
  - name: "readonly_data"
    features:
      pagination:
        enabled: true
        default_page_size: 5
        max_page_size: 50
      filtering:
        enabled: false
      sorting:
        enabled: false
```

### Search Table

```yaml
tables:
  - name: "search_results"
    features:
      pagination:
        enabled: false  # No pagination for search
      filtering:
        enabled: true   # Advanced filtering
      sorting:
        enabled: true   # Sort by relevance
```

## Best Practices

1. **Set Appropriate Page Sizes**: Balance performance with user experience
2. **Index Filtered Fields**: Ensure database indexes on filtered columns
3. **Limit Max Page Size**: Prevent excessive data transfer
4. **Use Filtering Wisely**: Avoid filtering on unindexed fields
5. **Combine Features**: Use pagination + filtering + sorting together

## Examples

For complete examples, see:
- [Features Config Example](https://github.com/iklobato/pylight/blob/main/docs/examples/yaml_configs/features_config.yaml)
- [REST Endpoints](rest-endpoints.md) for REST API examples
- [GraphQL](graphql.md) for GraphQL examples

## Next Steps

- Learn about [Caching](caching.md) for performance
- Explore [YAML Configuration](yaml-configuration.md) for complex setups
- Check out [Use Cases](../use-cases/index.md) for real-world patterns

