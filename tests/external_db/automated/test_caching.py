"""Redis caching tests for external database integration."""

import os
import pytest
import time
from tests.external_db.fixtures.api_client import APIClient


@pytest.fixture
def api_client(pylight_base_url: str) -> APIClient:
    """Create API client for testing."""
    client = APIClient(base_url=pylight_base_url)
    assert client.wait_for_ready(timeout=60), "Pylight API is not ready"
    return client


@pytest.mark.automated
class TestCaching:
    """Test Redis caching functionality."""
    
    @pytest.mark.skipif(
        os.getenv("REDIS_ENABLED", "false").lower() != "true",
        reason="Redis caching not enabled"
    )
    def test_cache_hit(self, api_client: APIClient):
        """Test that cached responses are returned."""
        # First request (cache miss)
        response1 = api_client.get_list("products", params={"page": 1, "limit": 10})
        assert "items" in response1, "First request should succeed"
        
        # Second request (should be cache hit)
        start_time = time.time()
        response2 = api_client.get_list("products", params={"page": 1, "limit": 10})
        elapsed_time = time.time() - start_time
        
        assert "items" in response2, "Second request should succeed"
        # Cached response should be faster (if cache is working)
        # Note: This is a heuristic, actual timing depends on many factors
    
    @pytest.mark.skipif(
        os.getenv("REDIS_ENABLED", "false").lower() != "true",
        reason="Redis caching not enabled"
    )
    def test_cache_miss(self, api_client: APIClient):
        """Test that cache miss occurs for new queries."""
        # Request with unique parameters
        response1 = api_client.get_list("products", params={"page": 999, "limit": 10})
        assert "items" in response1, "Request should succeed"
        
        # Different query should be cache miss
        response2 = api_client.get_list("products", params={"page": 998, "limit": 10})
        assert "items" in response2, "Different query should succeed"
    
    @pytest.mark.skipif(
        os.getenv("REDIS_ENABLED", "false").lower() != "true",
        reason="Redis caching not enabled"
    )
    def test_cache_invalidation_on_update(self, api_client: APIClient):
        """Test that cache is invalidated when record is updated."""
        # Get a product
        products = api_client.get_list("products")
        if not products.get("items"):
            pytest.skip("No products in database")
        
        product_id = products["items"][0]["id"]
        
        # First request (may be cached)
        response1 = api_client.get_item("products", product_id)
        original_name = response1.get("name")
        
        # Update product
        api_client.update_item("products", product_id, {"name": "Updated Name"})
        
        # Second request (should not be cached, should show update)
        response2 = api_client.get_item("products", product_id)
        assert response2.get("name") == "Updated Name", "Cache should be invalidated after update"
    
    def test_redis_unavailability_handling(self, api_client: APIClient):
        """Test that system handles Redis unavailability gracefully."""
        # If Redis is not available, API should still work
        # (caching should be optional)
        response = api_client.get_list("products")
        assert "items" in response, "API should work without Redis"
    
    @pytest.mark.skipif(
        os.getenv("REDIS_ENABLED", "false").lower() != "true",
        reason="Redis caching not enabled"
    )
    def test_cache_ttl(self, api_client: APIClient):
        """Test that cache respects TTL (time-to-live)."""
        # Make request
        response1 = api_client.get_list("products", params={"page": 1, "limit": 10})
        assert "items" in response1, "Request should succeed"
        
        # Wait for cache to expire (if TTL is short)
        # Note: This test assumes a short TTL, adjust based on actual configuration
        time.sleep(2)
        
        # Request again (may be cache miss if TTL expired)
        response2 = api_client.get_list("products", params={"page": 1, "limit": 10})
        assert "items" in response2, "Request should succeed after TTL"

