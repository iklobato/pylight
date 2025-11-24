"""Example: GraphQL Queries and Mutations Validation

This script validates that GraphQL queries, mutations, filtering, and GraphiQL interface work correctly.
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
BASE_URL = "http://127.0.0.1:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql"
GRAPHIQL_URL = f"{BASE_URL}/graphiql"


def main():
    """Run GraphQL validation example."""
    print("=" * 60)
    print("GraphQL Queries and Mutations Validation Example")
    print("=" * 60)

    # Verify dependencies
    print("\n1. Verifying dependencies...")
    if not verify_postgres():
        sys.exit(1)
    print("   ✓ PostgreSQL connection verified")

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

        # Test GraphQL Query - Retrieve products list
        print("\n3. Testing GraphQL query - products list...")
        query = """
        query {
            products {
                id
                name
                price
                description
                createdAt
            }
        }
        """
        response = requests.post(
            GRAPHQL_URL, json={"query": query}, headers={"Content-Type": "application/json"}, timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data" in data, "Response missing 'data' field"
        assert "products" in data["data"], "Response missing 'products' field"
        print("   ✓ GraphQL query executed successfully")

        # Test GraphQL Mutation - Create product
        print("\n4. Testing GraphQL mutation - create product...")
        mutation = """
        mutation {
            createProduct(name: "test_GraphQL Product", price: 150, description: "GraphQL test product") {
                id
                name
                price
                description
                createdAt
            }
        }
        """
        response = requests.post(
            GRAPHQL_URL, json={"query": mutation}, headers={"Content-Type": "application/json"}, timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data" in data, "Response missing 'data' field"
        assert "createProduct" in data["data"], "Response missing 'createProduct' field"
        created_product = data["data"]["createProduct"]
        assert "id" in created_product, "Created product missing 'id'"
        product_id = created_product["id"]
        print(f"   ✓ Product created via GraphQL with ID: {product_id}")

        # Validate database state after GraphQL mutation
        print("\n5. Validating database state after GraphQL mutation...")
        db_record = verify_database_state(session, "products", product_id)
        assert db_record is not None, "Product not found in database"
        assert db_record["name"] == "test_GraphQL Product", "Database name mismatch"
        assert db_record["price"] == 150, "Database price mismatch"
        print("   ✓ Database state validated")

        # Test GraphQL Filtering
        print("\n6. Testing GraphQL filtering...")
        filter_query = """
        query {
            products(filter: {name: "test_GraphQL"}) {
                id
                name
                price
            }
        }
        """
        response = requests.post(
            GRAPHQL_URL,
            json={"query": filter_query},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "data" in data, "Response missing 'data' field"
        products = data["data"]["products"]
        # Verify all returned products match filter
        for product in products:
            assert "test_GraphQL" in product["name"], f"Product {product['name']} doesn't match filter"
        print("   ✓ GraphQL filtering works correctly")

        # Test GraphiQL interface
        print("\n7. Testing GraphiQL interface...")
        response = requests.get(GRAPHIQL_URL, timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "text/html" in response.headers.get("Content-Type", ""), "GraphiQL not returning HTML"
        print("   ✓ GraphiQL interface accessible")

        # Cleanup test data
        print("\n8. Cleaning up test data...")
        cleanup_test_data(session, "products", "test_")
        print("   ✓ Test data cleaned up")

        print("\n" + "=" * 60)
        print("✓ All GraphQL tests passed!")
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

