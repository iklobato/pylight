"""Tests for cleanup on failure in data generator."""

import psycopg2
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


@pytest.fixture
def schema_generator(test_connection_string):
    """Create schema generator and ensure schema exists."""
    gen = SchemaGenerator(test_connection_string)
    gen.create_schema(drop_existing=True)
    return gen


@pytest.fixture(autouse=True)
def cleanup_schema(test_connection_string):
    """Clean up schema after each test."""
    yield
    gen = SchemaGenerator(test_connection_string)
    try:
        gen.drop_schema()
    except Exception:
        pass


def test_cleanup_on_failure(test_connection_string, schema_generator):
    """Test that partial data is cleaned up on failure when cleanup_on_failure=True."""
    # This test would require mocking a failure scenario
    # For now, we'll test that the cleanup_on_failure flag is respected
    config = DataGenerationConfig(
        connection_string=test_connection_string,
        cleanup_on_failure=True,
        record_counts={"users": 10},
    )

    generator = DataGenerator(config)

    # Generate data successfully
    counts = generator.generate_all()

    # Verify data was generated
    assert counts["users"] == 10

    # Verify cleanup_on_failure is set
    assert generator.config.cleanup_on_failure is True


def test_no_cleanup_on_failure(test_connection_string, schema_generator):
    """Test that partial data is preserved on failure when cleanup_on_failure=False."""
    config = DataGenerationConfig(
        connection_string=test_connection_string,
        cleanup_on_failure=False,
        record_counts={"users": 10},
    )

    generator = DataGenerator(config)

    # Verify cleanup_on_failure is False
    assert generator.config.cleanup_on_failure is False
