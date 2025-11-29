"""REST CRUD operations tests for external database integration."""

import pytest
from tests.external_db.fixtures.api_client import APIClient
from tests.external_db.fixtures.database_client import DatabaseClient
from tests.external_db.fixtures.test_data import TABLES, SAMPLE_PRODUCT, SAMPLE_USER, SAMPLE_ORDER


@pytest.fixture
def api_client(pylight_base_url: str) -> APIClient:
    """Create API client for testing."""
    client = APIClient(base_url=pylight_base_url)
    # Wait for API to be ready
    assert client.wait_for_ready(timeout=60), "Pylight API is not ready"
    return client


@pytest.fixture
def db_client(database_url: str) -> DatabaseClient:
    """Create database client for verification."""
    return DatabaseClient(connection_string=database_url)


@pytest.mark.automated
class TestRESTCRUD:
    """Test REST CRUD operations for all tables."""
    
    @pytest.mark.parametrize("table_name", TABLES)
    def test_get_list(self, api_client: APIClient, table_name: str):
        """Test GET /api/{table_name} returns list of records."""
        response = api_client.get_list(table_name)
        
        assert "items" in response or isinstance(response, list), f"Response should contain items for {table_name}"
        assert isinstance(response.get("items", response), list), f"Items should be a list for {table_name}"
    
    @pytest.mark.parametrize("table_name", ["products", "users", "orders"])
    def test_get_item(self, api_client: APIClient, db_client: DatabaseClient, table_name: str):
        """Test GET /api/{table_name}/{id} returns single record."""
        # Get first record ID from database
        with db_client:
            db_client.connect()
            records = db_client.execute_query(f"SELECT id FROM {table_name} LIMIT 1")
            if not records:
                pytest.skip(f"No records in {table_name}")
            record_id = records[0]['id']
        
        # Get record via API
        response = api_client.get_item(table_name, record_id)
        
        assert "id" in response or response.get("id") == record_id, f"Response should contain record ID for {table_name}"
    
    def test_create_product(self, api_client: APIClient, db_client: DatabaseClient):
        """Test POST /api/products creates new record."""
        # Create new product with unique SKU to avoid conflicts
        import time
        unique_product = SAMPLE_PRODUCT.copy()
        unique_product["sku"] = f"TEST-SKU-{int(time.time() * 1000)}"
        response = api_client.create_item("products", unique_product)
        
        assert "id" in response, "Response should contain created record ID"
        product_id = response["id"]
        
        # Verify in database
        with db_client:
            db_client.connect()
            assert db_client.verify_record_exists("products", product_id), "Product should exist in database"
    
    def test_update_product(self, api_client: APIClient, db_client: DatabaseClient):
        """Test PUT /api/products/{id} updates existing record."""
        # Get existing product
        with db_client:
            db_client.connect()
            records = db_client.execute_query("SELECT id FROM products LIMIT 1")
            if not records:
                pytest.skip("No products in database")
            product_id = records[0]['id']
        
        # Update product
        update_data = {"name": "Updated Product Name", "price": "199.99"}
        response = api_client.update_item("products", product_id, update_data)
        
        assert response.get("name") == "Updated Product Name", "Product name should be updated"
        
        # Verify in database
        with db_client:
            db_client.connect()
            record = db_client.get_table_record("products", product_id)
            assert record["name"] == "Updated Product Name", "Product should be updated in database"
    
    def test_delete_product(self, api_client: APIClient, db_client: DatabaseClient):
        """Test DELETE /api/products/{id} removes record."""
        # Create a product to delete with unique SKU to avoid conflicts
        import time
        unique_product = SAMPLE_PRODUCT.copy()
        unique_product["sku"] = f"DELETE-SKU-{int(time.time() * 1000)}"
        create_response = api_client.create_item("products", unique_product)
        product_id = create_response["id"]
        
        # Verify it exists
        with db_client:
            db_client.connect()
            assert db_client.verify_record_exists("products", product_id), "Product should exist before deletion"
        
        # Delete product
        success = api_client.delete_item("products", product_id)
        assert success, "Delete should succeed"
        
        # Verify deleted
        with db_client:
            db_client.connect()
            assert db_client.verify_record_deleted("products", product_id), "Product should be deleted from database"
    
    @pytest.mark.parametrize("table_name", TABLES)
    def test_table_accessible(self, api_client: APIClient, table_name: str):
        """Test that all configured tables are accessible via REST endpoints."""
        try:
            response = api_client.get_list(table_name)
            assert response is not None, f"Table {table_name} should be accessible"
        except Exception as e:
            pytest.fail(f"Table {table_name} is not accessible: {e}")

