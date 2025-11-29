"""GraphQL queries and mutations tests for external database integration."""

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
class TestGraphQL:
    """Test GraphQL queries and mutations."""
    
    def test_graphql_query_list(self, api_client: APIClient):
        """Test GraphQL query to list items."""
        query = """
        query {
            products {
                id
                name
                price
            }
        }
        """
        
        response = api_client.post("/graphql", json={"query": query})
        assert response.status_code == 200, "GraphQL query should succeed"
        
        data = response.json()
        assert "data" in data, "Response should contain data"
        assert "products" in data["data"], "Response should contain products"
        assert isinstance(data["data"]["products"], list), "Products should be a list"
    
    def test_graphql_query_single_item(self, api_client: APIClient, db_client: DatabaseClient):
        """Test GraphQL query for single item."""
        # Get product ID from database
        with db_client:
            db_client.connect()
            records = db_client.execute_query("SELECT id FROM products LIMIT 1")
            if not records:
                pytest.skip("No products in database")
            product_id = records[0]['id']
        
        query = f"""
        query {{
            product(id: {product_id}) {{
                id
                name
                price
            }}
        }}
        """
        
        response = api_client.post("/graphql", json={"query": query})
        assert response.status_code == 200, "GraphQL query should succeed"
        
        data = response.json()
        assert "data" in data, "Response should contain data"
        assert "product" in data["data"], "Response should contain product"
        assert data["data"]["product"]["id"] == product_id, "Should return correct product"
    
    def test_graphql_mutation_create(self, api_client: APIClient, db_client: DatabaseClient):
        """Test GraphQL mutation to create item."""
        import time
        unique_sku = f"GQL-{int(time.time() * 1000)}"
        mutation = f"""
        mutation {{
            createProduct(input: {{
                name: "GraphQL Test Product"
                price: "199.99"
                sku: "{unique_sku}"
            }}) {{
                id
                name
                price
            }}
        }}
        """
        
        response = api_client.post("/graphql", json={"query": mutation})
        assert response.status_code == 200, "GraphQL mutation should succeed"
        
        data = response.json()
        assert "data" in data, "Response should contain data"
        assert "createProduct" in data["data"], "Response should contain createProduct"
        
        product = data["data"]["createProduct"]
        assert "id" in product, "Created product should have ID"
        
        # Verify in database
        product_id = product["id"]
        with db_client:
            db_client.connect()
            assert db_client.verify_record_exists("products", product_id), "Product should exist in database"
    
    def test_graphql_mutation_update(self, api_client: APIClient, db_client: DatabaseClient):
        """Test GraphQL mutation to update item."""
        # Get existing product
        with db_client:
            db_client.connect()
            records = db_client.execute_query("SELECT id FROM products LIMIT 1")
            if not records:
                pytest.skip("No products in database")
            product_id = records[0]['id']
        
        mutation = f"""
        mutation {{
            updateProduct(id: {product_id}, input: {{
                name: "Updated via GraphQL"
            }}) {{
                id
                name
            }}
        }}
        """
        
        response = api_client.post("/graphql", json={"query": mutation})
        assert response.status_code == 200, "GraphQL mutation should succeed"
        
        data = response.json()
        assert "data" in data, "Response should contain data"
        assert "updateProduct" in data["data"], "Response should contain updateProduct"
        assert data["data"]["updateProduct"]["name"] == "Updated via GraphQL", "Product should be updated"
    
    def test_graphql_mutation_delete(self, api_client: APIClient, db_client: DatabaseClient):
        """Test GraphQL mutation to delete item."""
        # Create product to delete
        create_mutation = """
        mutation {
            createProduct(input: {
                name: "To Delete"
                price: "99.99"
                sku: "DELETE-001"
            }) {
                id
            }
        }
        """
        
        create_response = api_client.post("/graphql", json={"query": create_mutation})
        product_id = create_response.json()["data"]["createProduct"]["id"]
        
        # Delete product
        delete_mutation = f"""
        mutation {{
            deleteProduct(id: {product_id}) {{
                id
            }}
        }}
        """
        
        response = api_client.post("/graphql", json={"query": delete_mutation})
        assert response.status_code == 200, "GraphQL mutation should succeed"
        
        # Verify deleted
        with db_client:
            db_client.connect()
            assert db_client.verify_record_deleted("products", product_id), "Product should be deleted"
    
    def test_graphql_schema_validation(self, api_client: APIClient):
        """Test GraphQL schema is correctly generated from database structure."""
        # Introspection query
        query = """
        query {
            __schema {
                types {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        }
        """
        
        response = api_client.post("/graphql", json={"query": query})
        assert response.status_code == 200, "Introspection query should succeed"
        
        data = response.json()
        assert "data" in data, "Response should contain data"
        assert "__schema" in data["data"], "Response should contain schema"
        
        # Verify Product type exists
        types = data["data"]["__schema"]["types"]
        type_names = [t["name"] for t in types]
        assert "Product" in type_names or "product" in type_names.lower(), "Product type should exist in schema"

