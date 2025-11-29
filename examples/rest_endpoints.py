"""Example: REST Endpoints Validation

This script validates that REST endpoints (GET, POST, PUT, DELETE) work correctly
with database state validation.
"""

import sys
import os
import requests

# Add parent directory to path to import framework
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from docs.examples.test_models import Product
from docs.examples.utils import (
    verify_postgres,
    start_server,
    wait_for_server,
    stop_server,
    setup_server_cleanup,
)
from docs.examples.db_utils import (
    create_database_connection,
    verify_database_state,
    cleanup_test_data,
)

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/pylight"
BASE_URL = "http://127.0.0.1:8001"  # Use different port to avoid conflicts


def main():
    """Run REST endpoints validation example."""
    print("=" * 60)
    print("REST Endpoints Validation Example")
    print("=" * 60)

    # Verify dependencies
    print("\n1. Verifying dependencies...")
    if not verify_postgres():
        sys.exit(1)
    print("   ✓ PostgreSQL connection verified")

    # Start server using app_module
    print("\n2. Starting server...")
    # Change to examples directory for uvicorn to find the module
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    original_cwd = os.getcwd()
    os.chdir(examples_dir)
    try:
        server_process = start_server("app_module:starlette_app")
    finally:
        os.chdir(original_cwd)
    if server_process is None:
        print("   ✗ Failed to start server")
        sys.exit(1)

    setup_server_cleanup(server_process)

    if not wait_for_server():
        print("   ✗ Server failed to start within timeout")
        stop_server(server_process)
        sys.exit(1)
    print("   ✓ Server started on http://127.0.0.1:8001")

    # Create database connection
    engine, Session = create_database_connection(DATABASE_URL)
    session = Session()

    try:
        # Create tables if they don't exist
        Product.metadata.create_all(engine)

        # Test POST - Create product
        print("\n4. Testing POST /api/products...")
        product_data = {
            "name": "test_Product 1",
            "price": 100,
            "description": "Test product description",
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, timeout=10)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        created_product = response.json()
        assert "id" in created_product, "Response missing 'id' field"
        assert created_product["name"] == product_data["name"], "Name mismatch"
        assert created_product["price"] == product_data["price"], "Price mismatch"
        product_id = created_product["id"]
        print(f"   ✓ Product created with ID: {product_id}")

        # Validate database state after POST
        print("\n5. Validating database state after POST...")
        db_record = verify_database_state(session, "products", product_id)
        assert db_record is not None, "Product not found in database"
        assert db_record["name"] == product_data["name"], "Database name mismatch"
        assert db_record["price"] == product_data["price"], "Database price mismatch"
        print("   ✓ Database state validated")

        # Test GET - List products with pagination
        print("\n6. Testing GET /api/products (list with pagination)...")
        response = requests.get(f"{BASE_URL}/api/products?page=1&limit=10", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        list_response = response.json()
        assert "items" in list_response, "Response missing 'items' field"
        assert "total" in list_response, "Response missing 'total' field"
        assert "page" in list_response, "Response missing 'page' field"
        print(f"   ✓ List retrieved: {len(list_response['items'])} items, page {list_response['page']}")

        # Test GET - Retrieve product by ID
        print("\n7. Testing GET /api/products/{id}...")
        response = requests.get(f"{BASE_URL}/api/products/{product_id}", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        retrieved_product = response.json()
        assert retrieved_product["id"] == product_id, "ID mismatch"
        assert retrieved_product["name"] == product_data["name"], "Name mismatch"
        print("   ✓ Product retrieved successfully")

        # Test GET - Filtering
        print("\n8. Testing GET /api/products with filtering...")
        response = requests.get(f"{BASE_URL}/api/products?name__eq=test_Product 1", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        filtered_response = response.json()
        assert "items" in filtered_response, "Filtered response missing 'items'"
        print("   ✓ Filtering works")

        # Test GET - Sorting
        print("\n9. Testing GET /api/products with sorting...")
        response = requests.get(f"{BASE_URL}/api/products?sort=-price", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        sorted_response = response.json()
        assert "items" in sorted_response, "Sorted response missing 'items'"
        print("   ✓ Sorting works")

        # Validate database state after GET
        print("\n10. Validating database state after GET...")
        db_record = verify_database_state(session, "products", product_id)
        assert db_record["name"] == retrieved_product["name"], "API-DB name mismatch"
        assert db_record["price"] == retrieved_product["price"], "API-DB price mismatch"
        print("   ✓ Database state matches API response")

        # Test PUT - Update product
        print("\n11. Testing PUT /api/products/{id}...")
        update_data = {
            "name": "test_Updated Product",
            "price": 200,
            "description": "Updated description",
        }
        response = requests.put(
            f"{BASE_URL}/api/products/{product_id}", json=update_data, timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        updated_product = response.json()
        assert updated_product["name"] == update_data["name"], "Name not updated"
        assert updated_product["price"] == update_data["price"], "Price not updated"
        print("   ✓ Product updated successfully")

        # Validate database state after PUT
        print("\n12. Validating database state after PUT...")
        db_record = verify_database_state(session, "products", product_id)
        assert db_record["name"] == update_data["name"], "Database name not updated"
        assert db_record["price"] == update_data["price"], "Database price not updated"
        print("   ✓ Database reflects updated values")

        # Test DELETE - Delete product
        print("\n13. Testing DELETE /api/products/{id}...")
        response = requests.delete(f"{BASE_URL}/api/products/{product_id}", timeout=10)
        assert response.status_code in [200, 204], f"Expected 200/204, got {response.status_code}"
        print("   ✓ Product deleted successfully")

        # Validate database state after DELETE
        print("\n14. Validating database state after DELETE...")
        db_record = verify_database_state(session, "products", product_id)
        assert db_record is None, "Product still exists in database after delete"
        print("   ✓ Product removed from database")

        # Cleanup test data
        print("\n15. Cleaning up test data...")
        cleanup_test_data(session, "products", "test_")
        print("   ✓ Test data cleaned up")

        print("\n" + "=" * 60)
        print("✓ All REST endpoint tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()
        stop_server(server_process)


if __name__ == "__main__":
    main()

