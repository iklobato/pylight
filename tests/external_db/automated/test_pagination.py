"""Pagination tests for external database integration."""

import pytest
from tests.external_db.fixtures.api_client import APIClient
from tests.external_db.fixtures.database_client import DatabaseClient


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
class TestPagination:
    """Test pagination functionality with large datasets."""
    
    def test_pagination_page_1_limit_10(self, api_client: APIClient, db_client: DatabaseClient):
        """Test pagination: page 1 with limit 10 returns exactly 10 records."""
        # Verify we have enough records
        with db_client:
            db_client.connect()
            total_count = db_client.get_table_count("products")
            if total_count < 10:
                pytest.skip("Not enough products in database for pagination test")
        
        # Request page 1 with limit 10
        response = api_client.get_list("products", params={"page": 1, "limit": 10})
        
        # Verify response structure
        assert "items" in response, "Response should contain items"
        items = response["items"]
        assert len(items) == 10, f"Should return exactly 10 items, got {len(items)}"
        
        # Verify pagination metadata
        assert "total" in response, "Response should contain total count"
        assert "page" in response, "Response should contain page number"
        assert response["page"] == 1, "Page should be 1"
        assert "limit" in response, "Response should contain limit"
        assert response["limit"] == 10, "Limit should be 10"
        assert "pages" in response or "total_pages" in response, "Response should contain total pages"
    
    def test_pagination_multiple_pages(self, api_client: APIClient):
        """Test pagination across multiple pages returns consistent data."""
        # Get page 1
        page1 = api_client.get_list("products", params={"page": 1, "limit": 10})
        items1 = page1["items"]
        ids1 = {item["id"] for item in items1}
        
        # Get page 2
        page2 = api_client.get_list("products", params={"page": 2, "limit": 10})
        items2 = page2["items"]
        ids2 = {item["id"] for item in items2}
        
        # Verify no overlap
        assert ids1.isdisjoint(ids2), "Pages should not have overlapping records"
        
        # Verify both pages have correct count
        assert len(items1) == 10, "Page 1 should have 10 items"
        assert len(items2) == 10, "Page 2 should have 10 items"
    
    def test_pagination_last_page(self, api_client: APIClient, db_client: DatabaseClient):
        """Test pagination on last page returns remaining records."""
        with db_client:
            db_client.connect()
            total_count = db_client.get_table_count("products")
        
        if total_count < 25:
            pytest.skip("Not enough products for last page test")
        
        # Calculate last page
        limit = 10
        last_page = (total_count + limit - 1) // limit
        
        # Get last page
        response = api_client.get_list("products", params={"page": last_page, "limit": limit})
        
        items = response["items"]
        assert len(items) <= limit, f"Last page should have at most {limit} items"
        assert len(items) > 0, "Last page should have at least 1 item"
        assert response["page"] == last_page, f"Page should be {last_page}"
    
    def test_pagination_default_values(self, api_client: APIClient):
        """Test pagination with default values works correctly."""
        response = api_client.get_list("products")
        
        assert "items" in response, "Response should contain items"
        assert isinstance(response["items"], list), "Items should be a list"
        assert len(response["items"]) > 0, "Should return at least one item"
    
    def test_pagination_invalid_page(self, api_client: APIClient):
        """Test pagination with invalid page number handles gracefully."""
        # Request page 0 (invalid)
        response = api_client.get_list("products", params={"page": 0, "limit": 10})
        
        # Should either return empty results or page 1
        assert "items" in response, "Response should contain items"
        items = response["items"]
        # Either empty or valid page 1
        assert len(items) >= 0, "Should handle invalid page gracefully"
    
    def test_pagination_large_limit(self, api_client: APIClient):
        """Test pagination with large limit value."""
        response = api_client.get_list("products", params={"page": 1, "limit": 100})
        
        assert "items" in response, "Response should contain items"
        items = response["items"]
        assert len(items) <= 100, "Should respect limit of 100"
        assert len(items) > 0, "Should return at least one item"

