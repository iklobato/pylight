# My API

A Pylight API project.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your database in `config.yaml`

3. Run the application:
   ```bash
   python main.py
   ```

4. Access the API:
   - REST API: http://localhost:8000/api/
   - GraphQL: http://localhost:8000/graphql
   - GraphiQL: http://localhost:8000/graphiql
   - Swagger Docs: http://localhost:8000/docs

## Models

This project includes starter models:
- **User**: Application users with authentication
- **Project**: Projects containing tasks
- **Task**: Tasks with status, assignee, and project relationships

## Customization

Edit models in `src/models/` and register them in `main.py`:

```python
from src.models.my_model import MyModel

app.register(MyModel)
```

