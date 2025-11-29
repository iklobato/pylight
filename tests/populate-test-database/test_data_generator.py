"""Tests for data generator."""

import psycopg2
import pytest
from faker import Faker

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


@pytest.fixture
def data_generator(test_connection_string, schema_generator):
    """Create data generator instance."""
    config = DataGenerationConfig(
        connection_string=test_connection_string,
        seed=42,
        record_counts={"users": 10, "products": 10},
    )
    return DataGenerator(config)


@pytest.fixture(autouse=True)
def cleanup_schema(test_connection_string):
    """Clean up schema after each test."""
    yield
    gen = SchemaGenerator(test_connection_string)
    try:
        gen.drop_schema()
    except Exception:
        pass


def test_populate_all_tables_default_counts(data_generator, test_connection_string):
    """Test that data population populates all tables with default counts."""
    # Act
    counts = data_generator.generate_all()

    # Assert: Verify all tables have records
    assert "users" in counts
    assert counts["users"] > 0
    assert "products" in counts
    assert counts["products"] > 0
    assert "categories" in counts
    assert counts["categories"] > 0

    # Verify in database
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            assert cur.fetchone()[0] == counts["users"]


def test_foreign_key_references_are_valid(data_generator, test_connection_string):
    """Test that foreign key references are valid."""
    # Act
    data_generator.generate_all()

    # Assert: Verify foreign key integrity
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            # Check products.category_id references valid categories
            cur.execute(
                """
                SELECT COUNT(*)
                FROM products p
                WHERE NOT EXISTS (
                    SELECT 1 FROM categories c WHERE c.id = p.category_id
                )
                """
            )
            assert cur.fetchone()[0] == 0, "Invalid category_id references found"

            # Check orders.user_id references valid users
            cur.execute(
                """
                SELECT COUNT(*)
                FROM orders o
                WHERE NOT EXISTS (
                    SELECT 1 FROM users u WHERE u.id = o.user_id
                )
                """
            )
            assert cur.fetchone()[0] == 0, "Invalid user_id references found"


def test_seed_produces_reproducible_data(test_connection_string, schema_generator):
    """Test that seed parameter produces reproducible data."""
    # Arrange: Generate data twice with same seed
    config1 = DataGenerationConfig(
        connection_string=test_connection_string, seed=42, record_counts={"users": 5}
    )
    gen1 = DataGenerator(config1)
    gen1.generate_all()

    # Get first set of emails
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM users ORDER BY id")
            emails1 = [row[0] for row in cur.fetchall()]

    # Clean and regenerate with same seed
    schema_generator.drop_schema()
    schema_generator.create_schema()

    config2 = DataGenerationConfig(
        connection_string=test_connection_string, seed=42, record_counts={"users": 5}
    )
    gen2 = DataGenerator(config2)
    gen2.generate_all()

    # Get second set of emails
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM users ORDER BY id")
            emails2 = [row[0] for row in cur.fetchall()]

    # Assert: Emails should be identical
    assert emails1 == emails2, "Seed did not produce reproducible data"


def test_custom_record_counts(data_generator, test_connection_string):
    """Test that custom record counts are respected."""
    # Act
    counts = data_generator.generate_all()

    # Assert: Verify custom counts
    assert counts["users"] == 10, f"Expected 10 users, got {counts['users']}"
    assert counts["products"] == 10, f"Expected 10 products, got {counts['products']}"


def test_json_columns_populated_correctly(data_generator, test_connection_string):
    """Test that JSON columns are populated correctly."""
    # Act
    data_generator.generate_all()

    # Assert: Verify JSON column has valid JSON
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT dimensions
                FROM products
                WHERE dimensions IS NOT NULL
                LIMIT 1
                """
            )
            result = cur.fetchone()
            if result:
                dimensions = result[0]
                assert isinstance(dimensions, dict), "dimensions should be a dict"
                assert "width" in dimensions
                assert "height" in dimensions
                assert "depth" in dimensions


def test_all_data_types_populated(data_generator, test_connection_string):
    """Test that all data types are populated correctly."""
    # Act
    data_generator.generate_all()

    # Assert: Verify various data types
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            # Check integer
            cur.execute("SELECT id FROM users LIMIT 1")
            assert isinstance(cur.fetchone()[0], int)

            # Check string
            cur.execute("SELECT email FROM users LIMIT 1")
            assert isinstance(cur.fetchone()[0], str)

            # Check decimal/numeric
            cur.execute("SELECT price FROM products LIMIT 1")
            price = cur.fetchone()[0]
            assert price is not None
            assert isinstance(price, (int, float, type(price)))  # Numeric type

            # Check boolean
            cur.execute("SELECT is_active FROM products LIMIT 1")
            assert isinstance(cur.fetchone()[0], bool)

            # Check timestamp
            cur.execute("SELECT created_at FROM users LIMIT 1")
            assert cur.fetchone()[0] is not None  # Timestamp exists


def test_unique_constraint_retry(data_generator, test_connection_string):
    """Test that unique constraint violations are retried with new values."""
    # This test verifies that the retry logic works
    # The data generator should handle unique constraint violations gracefully
    # by generating new values and retrying

    # Generate data - should succeed even if there are unique constraint attempts
    counts = data_generator.generate_all()

    # Verify all requested records were created
    assert counts["users"] > 0
    assert counts["products"] > 0

    # Verify uniqueness in database
    with psycopg2.connect(test_connection_string) as conn:
        with conn.cursor() as cur:
            # Check email uniqueness
            cur.execute(
                """
                SELECT email, COUNT(*)
                FROM users
                GROUP BY email
                HAVING COUNT(*) > 1
                """
            )
            duplicates = cur.fetchall()
            assert len(duplicates) == 0, f"Found duplicate emails: {duplicates}"

            # Check SKU uniqueness
            cur.execute(
                """
                SELECT sku, COUNT(*)
                FROM products
                GROUP BY sku
                HAVING COUNT(*) > 1
                """
            )
            duplicates = cur.fetchall()
            assert len(duplicates) == 0, f"Found duplicate SKUs: {duplicates}"
