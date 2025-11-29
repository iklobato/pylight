"""Tests for schema generator."""

import psycopg2
import pytest
from sqlalchemy import inspect, text

from scripts.populate_test_database.exceptions import SchemaError
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
    """Create schema generator instance."""
    return SchemaGenerator(test_connection_string)


@pytest.fixture(autouse=True)
def cleanup_schema(test_connection_string):
    """Clean up schema before and after each test."""
    # Setup: drop all tables
    gen = SchemaGenerator(test_connection_string)
    try:
        gen.drop_schema()
    except Exception:
        pass  # Ignore errors if schema doesn't exist

    yield

    # Teardown: drop all tables
    try:
        gen.drop_schema()
    except Exception:
        pass


def test_create_schema_creates_all_tables(schema_generator, test_connection_string):
    """Test that schema creation creates all 10+ tables."""
    # Act
    schema_generator.create_schema()

    # Assert: Verify all tables exist
    expected_tables = [
        "users",
        "categories",
        "products",
        "addresses",
        "orders",
        "order_items",
        "reviews",
        "payments",
        "shipments",
        "inventory",
    ]

    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in cur.fetchall()]

    for table in expected_tables:
        assert table in tables, f"Table '{table}' was not created"


def test_foreign_keys_are_created(schema_generator, test_connection_string):
    """Test that foreign key constraints are properly created."""
    # Arrange
    schema_generator.create_schema()

    # Act & Assert: Verify foreign keys exist
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            # Check products.category_id -> categories.id
            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_name = 'products'
                AND constraint_name LIKE '%category_id%'
                """
            )
            assert cur.fetchone()[0] > 0, "products.category_id foreign key not found"

            # Check orders.user_id -> users.id
            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_name = 'orders'
                AND constraint_name LIKE '%user_id%'
                """
            )
            assert cur.fetchone()[0] > 0, "orders.user_id foreign key not found"

            # Check order_items.order_id -> orders.id
            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_name = 'order_items'
                AND constraint_name LIKE '%order_id%'
                """
            )
            assert cur.fetchone()[0] > 0, "order_items.order_id foreign key not found"


def test_json_columns_are_created(schema_generator, test_connection_string):
    """Test that JSON/JSONB column types are correctly defined."""
    # Arrange
    schema_generator.create_schema()

    # Act & Assert: Verify JSON column exists in products table
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = 'products'
                AND column_name = 'dimensions'
                """
            )
            result = cur.fetchone()
            assert result is not None, "dimensions column not found"
            assert result[0] in (
                "json",
                "jsonb",
            ), f"dimensions column is not JSON type, got {result[0]}"


def test_drop_and_recreate_schema(schema_generator, test_connection_string):
    """Test that schema can be dropped and recreated."""
    # Arrange: Create schema and add some data
    schema_generator.create_schema()

    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, first_name, last_name) VALUES ('test@example.com', 'Test', 'User')"
            )
            conn.commit()

    # Act: Drop and recreate
    schema_generator.drop_schema()
    schema_generator.create_schema()

    # Assert: Schema is recreated (tables exist) and data is gone
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            # Verify table exists
            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'users'
                """
            )
            assert cur.fetchone()[0] == 1, "users table was not recreated"

            # Verify data is gone
            cur.execute("SELECT COUNT(*) FROM users")
            assert cur.fetchone()[0] == 0, "Data was not cleaned up"
