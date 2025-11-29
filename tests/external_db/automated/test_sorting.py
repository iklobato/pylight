"""Sorting tests for external database integration."""

import pytest
from tests.external_db.fixtures.api_client import APIClient


@pytest.fixture
def api_client(pylight_base_url: str) -> APIClient:
    """Create API client for testing."""
    client = APIClient(base_url=pylight_base_url)
    assert client.wait_for_ready(timeout=60), "Pylight API is not ready"
    return client


@pytest.mark.automated
class TestSorting:
    """Test sorting functionality."""
    
    def test_sort_ascending(self, api_client: APIClient):
        """Test sorting in ascending order."""
        response = api_client.get_list("products", params={"sort": "price"})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        if len(items) < 2:
            pytest.skip("Not enough products for sorting test")
        
        # Verify ascending order
        prices = [float(item.get("price", 0)) for item in items]
        assert prices == sorted(prices), "Items should be sorted in ascending order by price"
    
    def test_sort_descending(self, api_client: APIClient):
        """Test sorting in descending order (-price)."""
        response = api_client.get_list("products", params={"sort": "-price"})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        if len(items) < 2:
            pytest.skip("Not enough products for sorting test")
        
        # Verify descending order
        prices = [float(item.get("price", 0)) for item in items]
        assert prices == sorted(prices, reverse=True), "Items should be sorted in descending order by price"
    
    def test_sort_multiple_fields(self, api_client: APIClient):
        """Test sorting by multiple fields."""
        # Sort by category_id then price
        response = api_client.get_list("products", params={"sort": "category_id,price"})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        if len(items) < 2:
            pytest.skip("Not enough products for multi-field sorting test")
        
        # Verify multi-field sort
        # Items should be grouped by category_id, then sorted by price within each group
        prev_category = None
        prev_price = None
        
        for item in items:
            category = item.get("category_id")
            price = float(item.get("price", 0))
            
            if prev_category is not None:
                if category == prev_category:
                    # Within same category, prices should be ascending
                    assert price >= prev_price, "Within same category, prices should be ascending"
                else:
                    # Category should be ascending
                    assert category >= prev_category, "Categories should be in ascending order"
            
            prev_category = category
            prev_price = price
    
    def test_sort_combined_with_pagination(self, api_client: APIClient):
        """Test sorting combined with pagination."""
        # Get first page sorted
        page1 = api_client.get_list("products", params={"sort": "-price", "page": 1, "limit": 10})
        items1 = page1["items"]
        
        # Get second page sorted
        page2 = api_client.get_list("products", params={"sort": "-price", "page": 2, "limit": 10})
        items2 = page2["items"]
        
        if len(items1) < 10 or len(items2) < 10:
            pytest.skip("Not enough products for pagination + sorting test")
        
        # Verify both pages are sorted
        prices1 = [float(item.get("price", 0)) for item in items1]
        prices2 = [float(item.get("price", 0)) for item in items2]
        
        assert prices1 == sorted(prices1, reverse=True), "Page 1 should be sorted descending"
        assert prices2 == sorted(prices2, reverse=True), "Page 2 should be sorted descending"
        
        # Verify page 2 prices are all <= page 1 prices (since descending)
        assert max(prices2) <= min(prices1), "Page 2 should have prices <= page 1 (descending sort)"
    
    def test_sort_combined_with_filtering(self, api_client: APIClient):
        """Test sorting combined with filtering."""
        # Filter and sort
        response = api_client.get_list("products", params={
            "price__gt": "100",
            "sort": "-price"
        })
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        
        if len(items) < 2:
            pytest.skip("Not enough filtered products for sorting test")
        
        # Verify filter and sort
        prices = [float(item.get("price", 0)) for item in items]
        
        # All should match filter
        for price in prices:
            assert price > 100, "All items should have price > 100"
        
        # Should be sorted descending
        assert prices == sorted(prices, reverse=True), "Items should be sorted in descending order"

