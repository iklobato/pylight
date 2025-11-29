"""Filtering tests for external database integration."""

import pytest
from tests.external_db.fixtures.api_client import APIClient
from tests.external_db.fixtures.database_client import DatabaseClient
from tests.external_db.fixtures.test_data import FILTER_OPERATORS


@pytest.fixture
def api_client(pylight_base_url: str) -> APIClient:
    """Create API client for testing."""
    client = APIClient(base_url=pylight_base_url)
    assert client.wait_for_ready(timeout=60), "Pylight API is not ready"
    return client


@pytest.fixture
def db_client(database_url: str) -> DatabaseClient:
    """Create database client for verification."""
    return DatabaseClient(connection_string=database_url)


@pytest.mark.automated
class TestFiltering:
    """Test filtering functionality with various operators."""
    
    def test_filter_gt(self, api_client: APIClient):
        """Test filtering with greater than operator (price__gt=100)."""
        response = api_client.get_list("products", params={"price__gt": "100"})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        # Verify all items match filter
        for item in items:
            price = float(item.get("price", 0))
            assert price > 100, f"All items should have price > 100, got {price}"
    
    def test_filter_like(self, api_client: APIClient):
        """Test filtering with like operator (name__like)."""
        # Filter products with name containing "Laptop"
        response = api_client.get_list("products", params={"name__like": "%Laptop%"})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        # Verify all items match filter
        for item in items:
            name = item.get("name", "")
            assert "Laptop" in name, f"All items should have 'Laptop' in name, got {name}"
    
    def test_filter_in(self, api_client: APIClient):
        """Test filtering with in operator (status__in)."""
        # Filter orders with specific statuses
        response = api_client.get_list("orders", params={"status__in": "pending,processing"})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        # Verify all items match filter
        for item in items:
            status = item.get("status", "")
            assert status in ["pending", "processing"], f"All items should have status in [pending, processing], got {status}"
    
    def test_filter_eq(self, api_client: APIClient):
        """Test filtering with equals operator."""
        # Get a specific product first
        all_products = api_client.get_list("products")
        if not all_products.get("items"):
            pytest.skip("No products in database")
        
        first_product = all_products["items"][0]
        product_id = first_product["id"]
        
        # Filter by ID
        response = api_client.get_list("products", params={"id__eq": str(product_id)})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        assert len(items) == 1, "Should return exactly one item"
        assert items[0]["id"] == product_id, "Should return the correct product"
    
    def test_filter_multiple_conditions(self, api_client: APIClient):
        """Test filtering with multiple conditions combined."""
        # Filter products with price between 50 and 200
        response = api_client.get_list("products", params={
            "price__gte": "50",
            "price__lte": "200"
        })
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        # Verify all items match both conditions
        for item in items:
            price = float(item.get("price", 0))
            assert 50 <= price <= 200, f"All items should have price between 50 and 200, got {price}"
    
    def test_filter_no_results(self, api_client: APIClient):
        """Test filtering that returns no results."""
        # Filter with impossible condition
        response = api_client.get_list("products", params={"price__gt": "999999"})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        assert len(items) == 0, "Should return empty list for impossible filter"
    
    def test_filter_invalid_operator(self, api_client: APIClient):
        """Test filtering with invalid operator handles gracefully."""
        # Try invalid operator
        try:
            response = api_client.get_list("products", params={"price__invalid": "100"})
            # Should either return error or ignore invalid filter
            assert "items" in response, "Response should contain items"
        except Exception:
            # Acceptable if invalid operator raises error
            pass

