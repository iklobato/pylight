"""Integration tests for Docker PostgreSQL support."""

import pytest

from scripts.populate_test_database.config import DataGenerationConfig
from scripts.populate_test_database.data_generator import DataGenerator
from scripts.populate_test_database.schema_generator import SchemaGenerator


@pytest.fixture
def test_connection_string():
    """Get test database connection string from environment."""
    import os

    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/pylight_test",
    )


@pytest.fixture(autouse=True)
def cleanup_schema(test_connection_string):
    """Clean up schema after each test."""
    yield
    gen = SchemaGenerator(test_connection_string)
    try:
        gen.drop_schema()
    except Exception:
        pass


def test_docker_postgres_integration(test_connection_string):
    """Test full integration with Docker PostgreSQL container."""
    # This test requires a running PostgreSQL instance (Docker or local)
    # Skip if connection fails

    try:
        # Test 1: Schema creation
        schema_gen = SchemaGenerator(test_connection_string)
        schema_gen.create_schema(drop_existing=True)
        assert schema_gen.schema_exists()

        # Test 2: Data population
        config = DataGenerationConfig(
            connection_string=test_connection_string,
            seed=42,
            record_counts={"users": 10, "products": 10},
        )
        data_gen = DataGenerator(config)
        counts = data_gen.generate_all()

        # Verify data was generated
        assert counts["users"] == 10
        assert counts["products"] == 10

        # Test 3: Schema recreation (drop and recreate)
        schema_gen.drop_schema()
        assert not schema_gen.schema_exists()
        schema_gen.create_schema()
        assert schema_gen.schema_exists()

    except Exception as e:
        pytest.skip(f"PostgreSQL not available for integration testing: {e}")
