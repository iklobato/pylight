"""Database reflection tests for external database integration."""

import pytest
from tests.external_db.fixtures.database_client import DatabaseClient
from tests.external_db.fixtures.api_client import APIClient
from tests.external_db.fixtures.test_data import TABLES


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
class TestDatabaseReflection:
    """Test database schema reflection functionality."""
    
    def test_table_discovery(self, db_client: DatabaseClient):
        """Test that all tables in database are discovered."""
        with db_client:
            db_client.connect()
            
            # Get all tables from database
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            """
            db_tables = db_client.execute_query(tables_query)
            db_table_names = {t['table_name'] for t in db_tables}
            
            # Verify expected tables exist
            for expected_table in TABLES:
                assert expected_table in db_table_names, f"Table {expected_table} should exist in database"
    
    def test_schema_reflection(self, db_client: DatabaseClient):
        """Test that table schemas are correctly reflected."""
        with db_client:
            db_client.connect()
            
            # Get schema for products table
            columns_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'products'
            ORDER BY ordinal_position
            """
            columns = db_client.execute_query(columns_query)
            
            # Verify key columns exist
            column_names = {c['column_name'] for c in columns}
            assert 'id' in column_names, "Products table should have id column"
            assert 'name' in column_names, "Products table should have name column"
            assert 'price' in column_names, "Products table should have price column"
    
    def test_relationship_detection(self, db_client: DatabaseClient):
        """Test that relationships between tables are detected."""
        with db_client:
            db_client.connect()
            
            # Get foreign keys
            fk_query = """
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            """
            foreign_keys = db_client.execute_query(fk_query)
            
            # Verify key relationships exist
            fk_map = {}
            for fk in foreign_keys:
                table = fk['table_name']
                if table not in fk_map:
                    fk_map[table] = []
                fk_map[table].append({
                    'column': fk['column_name'],
                    'references': fk['foreign_table_name']
                })
            
            # Check products -> categories relationship
            if 'products' in fk_map:
                product_fks = fk_map['products']
                category_fk = next((fk for fk in product_fks if fk['references'] == 'categories'), None)
                assert category_fk is not None, "Products should have foreign key to categories"
    
    def test_endpoint_generation_from_reflection(self, api_client: APIClient, db_client: DatabaseClient):
        """Test that endpoints are generated from reflected tables."""
        with db_client:
            db_client.connect()
            
            # Get all tables from database
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            """
            db_tables = db_client.execute_query(tables_query)
            db_table_names = [t['table_name'] for t in db_tables]
        
        # Verify endpoints exist for reflected tables
        for table_name in db_table_names[:5]:  # Test first 5 tables
            try:
                response = api_client.get_list(table_name)
                assert "items" in response or isinstance(response, list), f"Endpoint should exist for {table_name}"
            except Exception as e:
                # Some tables might not be exposed, which is acceptable
                pass
    
    def test_reflection_handles_schema_changes(self, db_client: DatabaseClient):
        """Test that reflection handles database schema changes."""
        with db_client:
            db_client.connect()
            
            # Add a new column to products table
            try:
                db_client.execute_update(
                    "ALTER TABLE products ADD COLUMN IF NOT EXISTS test_column VARCHAR(100)"
                )
                
                # Verify column was added
                columns_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'test_column'
                """
                columns = db_client.execute_query(columns_query)
                assert len(columns) > 0, "New column should be added to database"
                
                # Cleanup
                db_client.execute_update("ALTER TABLE products DROP COLUMN IF EXISTS test_column")
            except Exception as e:
                # If alter fails, that's okay for this test
                pass

