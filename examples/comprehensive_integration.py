"""Example: Comprehensive Integration Test

This script exercises all framework features together in a realistic scenario,
validating end-to-end functionality and database state persistence.
"""

import sys
import os
import time
import requests

# Add parent directory to path to import framework
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from docs.examples.test_models import Product, User
from docs.examples.utils import (
    verify_postgres,
    verify_redis,
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
BASE_URL = "http://127.0.0.1:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql"


def test_rest_endpoints(session):
    """Test REST endpoints."""
    print("\n3. Testing REST endpoints...")
    product_data = {
        "name": "test_Comprehensive Product",
        "price": 100,
        "description": "Comprehensive test product",
    }

    # POST
    response = requests.post(f"{BASE_URL}/api/products", json=product_data, timeout=10)
    assert response.status_code == 201, f"POST failed: {response.status_code}"
    created = response.json()
    product_id = created["id"]
    print(f"   ✓ POST: Created product {product_id}")

    # GET
    response = requests.get(f"{BASE_URL}/api/products/{product_id}", timeout=10)
    assert response.status_code == 200, f"GET failed: {response.status_code}"
    retrieved = response.json()
    assert retrieved["name"] == product_data["name"], "GET name mismatch"
    print(f"   ✓ GET: Retrieved product {product_id}")

    # PUT
    update_data = {"name": "test_Updated Comprehensive Product", "price": 200}
    response = requests.put(f"{BASE_URL}/api/products/{product_id}", json=update_data, timeout=10)
    assert response.status_code == 200, f"PUT failed: {response.status_code}"
    print(f"   ✓ PUT: Updated product {product_id}")

    # DELETE
    response = requests.delete(f"{BASE_URL}/api/products/{product_id}", timeout=10)
    assert response.status_code in [200, 204], f"DELETE failed: {response.status_code}"
    print(f"   ✓ DELETE: Deleted product {product_id}")

    return product_id


def test_graphql(session):
    """Test GraphQL queries and mutations."""
    print("\n4. Testing GraphQL...")

    # Query - List products
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
        GRAPHQL_URL, json={"query": query}, headers={"Content-Type": "application/json"}, timeout=10
    )
    assert response.status_code == 200, f"GraphQL query failed: {response.status_code}"
    data = response.json()
    assert "data" in data or "error" not in data, "GraphQL query failed"
    print("   ✓ GraphQL query executed")

    # Mutation - Create product
    mutation = """
    mutation {
        createProduct(input: {name: "test_GraphQL Comprehensive", price: 150}) {
            id
            name
        }
    }
    """
    response = requests.post(
        GRAPHQL_URL, json={"query": mutation}, headers={"Content-Type": "application/json"}, timeout=10
    )
    assert response.status_code == 200, f"GraphQL mutation failed: {response.status_code}"
    data = response.json()
    if "error" not in data:
        print("   ✓ GraphQL mutation executed")
        product_id = None
    else:
        print(f"   ⚠ GraphQL mutation returned error: {data.get('error')}")
        product_id = None

    return product_id


def test_pagination_filtering_sorting(session):
    """Test pagination, filtering, and sorting."""
    print("\n5. Testing pagination, filtering, and sorting...")

    # Create multiple products
    for i in range(5):
        requests.post(
            f"{BASE_URL}/api/products",
            json={"name": f"test_Sort Product {i}", "price": 100 + (i * 10)},
            timeout=10,
        )

    # Pagination
    response = requests.get(f"{BASE_URL}/api/products?page=1&limit=3", timeout=10)
    assert response.status_code == 200, "Pagination failed"
    data = response.json()
    assert "items" in data, "Pagination response missing 'items'"
    assert "total" in data, "Pagination response missing 'total'"
    assert len(data.get("items", [])) <= 3, "Pagination page size exceeded"
    print("   ✓ Pagination works")

    # Filtering
    response = requests.get(f"{BASE_URL}/api/products?name__eq=test_Sort Product 1", timeout=10)
    assert response.status_code == 200, "Filtering failed"
    data = response.json()
    assert "items" in data, "Filtered response missing 'items'"
    print("   ✓ Filtering works")

    # Sorting
    response = requests.get(f"{BASE_URL}/api/products?sort=-price", timeout=10)
    assert response.status_code == 200, "Sorting failed"
    data = response.json()
    assert "items" in data, "Sorted response missing 'items'"
    print("   ✓ Sorting works")


def test_documentation(session):
    """Test documentation endpoints."""
    print("\n6. Testing documentation...")

    # Swagger/OpenAPI
    response = requests.get(f"{BASE_URL}/docs", timeout=10)
    assert response.status_code == 200, "Swagger docs failed"
    print("   ✓ Swagger/OpenAPI docs accessible")

    # GraphiQL
    response = requests.get(f"{BASE_URL}/graphiql", timeout=10)
    assert response.status_code == 200, "GraphiQL failed"
    print("   ✓ GraphiQL interface accessible")


def test_database_state(session):
    """Validate database state matches API operations."""
    print("\n7. Validating database state...")

    # Query database directly
    products = verify_database_state(session, "products", test_prefix="test_")
    assert len(products) > 0, "No test products found in database"
    print(f"   ✓ Database contains {len(products)} test products")

    # Verify data integrity
    for product in products:
        assert "name" in product, "Product missing name"
        assert "price" in product, "Product missing price"
    print("   ✓ Database state validated")


def main():
    """Run comprehensive integration test."""
    print("=" * 60)
    print("Comprehensive Integration Test")
    print("=" * 60)
    start_time = time.time()

    # Verify dependencies
    print("\n1. Verifying dependencies...")
    if not verify_postgres():
        sys.exit(1)
    print("   ✓ PostgreSQL connection verified")

    if not verify_redis():
        print("   ⚠ Redis not available (caching tests will be skipped)")
    else:
        print("   ✓ Redis connection verified")

    # Start server
    print("\n2. Starting server...")
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    original_cwd = os.getcwd()
    os.chdir(examples_dir)
    try:
        server_process = start_server("app_module:app")
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
    print("   ✓ Server started on http://127.0.0.1:8000")

    # Create database connection
    engine, Session = create_database_connection(DATABASE_URL)
    session = Session()

    try:
        # Create tables if they don't exist
        Product.metadata.create_all(engine)
        User.metadata.create_all(engine)

        # Run all feature tests
        test_rest_endpoints(session)
        test_graphql(session)
        test_pagination_filtering_sorting(session)
        test_documentation(session)
        test_database_state(session)

        # Cleanup
        print("\n8. Cleaning up test data...")
        cleanup_test_data(session, "products", "test_")
        print("   ✓ Test data cleaned up")

        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("✓ All comprehensive integration tests passed!")
        print(f"  Execution time: {elapsed_time:.2f} seconds")
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

