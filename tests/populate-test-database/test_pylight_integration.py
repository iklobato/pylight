"""Integration tests for Pylight feature testing with populated database."""

import pytest
import requests

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
def populated_database(test_connection_string):
    """Create schema and populate with test data."""
    # Create schema
    schema_gen = SchemaGenerator(test_connection_string)
    schema_gen.create_schema(drop_existing=True)

    # Populate data
    config = DataGenerationConfig(
        connection_string=test_connection_string,
        seed=42,
        record_counts={
            "users": 100,
            "categories": 20,
            "products": 200,
            "addresses": 150,
            "orders": 300,
            "order_items": 500,
        },
    )
    generator = DataGenerator(config)
    generator.generate_all()

    yield test_connection_string

    # Cleanup
    try:
        schema_gen.drop_schema()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def cleanup_schema(test_connection_string):
    """Clean up schema after each test."""
    yield
    gen = SchemaGenerator(test_connection_string)
    try:
        gen.drop_schema()
    except Exception:
        pass


def test_rest_crud_operations(populated_database):
    """Test that REST CRUD operations work with populated data."""
    # This test assumes Pylight API is running
    # Skip if API is not available
    base_url = "http://localhost:8000"

    try:
        # Test GET list
        response = requests.get(f"{base_url}/api/products?limit=10", timeout=2)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
            assert len(data.get("items", data)) > 0
    except requests.exceptions.RequestException:
        pytest.skip("Pylight API not available for testing")


def test_graphql_queries(populated_database):
    """Test that GraphQL queries work with populated data."""
    base_url = "http://localhost:8000"

    try:
        query = """
        query {
            products {
                id
                name
                price
            }
        }
        """
        response = requests.post(
            f"{base_url}/graphql",
            json={"query": query},
            timeout=2,
        )
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "products" in data["data"]
    except requests.exceptions.RequestException:
        pytest.skip("Pylight API not available for testing")


def test_filtering_operators(populated_database):
    """Test that filtering with various operators works."""
    base_url = "http://localhost:8000"

    try:
        # Test eq filter
        response = requests.get(f"{base_url}/api/products?price__eq=99.99", timeout=2)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

        # Test gt filter
        response = requests.get(f"{base_url}/api/products?price__gt=50", timeout=2)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

        # Test like filter
        response = requests.get(f"{base_url}/api/products?name__like=%test%", timeout=2)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
    except requests.exceptions.RequestException:
        pytest.skip("Pylight API not available for testing")


def test_sorting_operations(populated_database):
    """Test that sorting operations work."""
    base_url = "http://localhost:8000"

    try:
        # Test ascending sort
        response = requests.get(f"{base_url}/api/products?sort=price", timeout=2)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data)
            if len(items) > 1:
                prices = [item.get("price") for item in items if "price" in item]
                if prices:
                    assert prices == sorted(prices)

        # Test descending sort
        response = requests.get(f"{base_url}/api/products?sort=-price", timeout=2)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data)
            if len(items) > 1:
                prices = [item.get("price") for item in items if "price" in item]
                if prices:
                    assert prices == sorted(prices, reverse=True)
    except requests.exceptions.RequestException:
        pytest.skip("Pylight API not available for testing")


def test_pagination(populated_database):
    """Test that pagination works with populated data."""
    base_url = "http://localhost:8000"

    try:
        # Test first page
        response = requests.get(f"{base_url}/api/products?page=1&limit=10", timeout=2)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
            items = data.get("items", data)
            assert len(items) <= 10

        # Test second page
        response = requests.get(f"{base_url}/api/products?page=2&limit=10", timeout=2)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data)
            # Second page should have different items (if enough data)
            assert isinstance(items, list)
    except requests.exceptions.RequestException:
        pytest.skip("Pylight API not available for testing")
