"""Application module for integration examples."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.presentation.app import LightApi
from docs.examples.test_models import Product, User

# Database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/pylight"

# Create app instance
app = LightApi(
    databaseUrl=DATABASE_URL,
    swaggerTitle="Integration Examples API",
    swaggerVersion="1.0.0",
)

# Register models
app.register(Product)
app.register(User)

# Export Starlette app for uvicorn
starlette_app = app.starletteApp

# For backward compatibility, also export as 'app'
app_instance = app

# Ensure database tables are created
if app.databaseManager:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    sync_engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))
    Product.metadata.create_all(sync_engine)
    User.metadata.create_all(sync_engine)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8001)

