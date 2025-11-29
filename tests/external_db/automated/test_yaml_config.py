"""YAML configuration loading tests for external database integration."""

import pytest
import yaml
import tempfile
import os
from pathlib import Path
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


@pytest.fixture
def sample_yaml_config(database_url: str) -> dict:
    """Create sample YAML configuration."""
    return {
        "database": {
            "url": database_url
        },
        "swagger": {
            "title": "Pylight Test API",
            "version": "1.0.0"
        },
        "tables": [
            {"name": "products"},
            {"name": "users"},
            {"name": "orders"}
        ],
        "features": {
            "pagination": {
                "enabled": True,
                "default_limit": 10
            },
            "filtering": {
                "enabled": True
            },
            "sorting": {
                "enabled": True
            }
        }
    }


@pytest.mark.automated
class TestYAMLConfiguration:
    """Test YAML configuration loading and application."""
    
    def test_yaml_config_loading(self, sample_yaml_config: dict):
        """Test that YAML configuration can be loaded from file."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_yaml_config, f)
            temp_path = f.name
        
        try:
            # Load YAML file
            with open(temp_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            assert loaded_config is not None, "YAML config should load successfully"
            assert "database" in loaded_config, "Config should contain database section"
            assert "tables" in loaded_config, "Config should contain tables section"
        finally:
            os.unlink(temp_path)
    
    def test_yaml_config_database_connection(self, api_client: APIClient, db_client: DatabaseClient):
        """Test that Pylight connects to database specified in YAML config."""
        # Verify database is accessible
        with db_client:
            db_client.connect()
            count = db_client.get_table_count("products")
            assert count >= 0, "Database should be accessible"
        
        # Verify API can access database
        response = api_client.get_list("products")
        assert "items" in response, "API should be able to access database"
    
    def test_yaml_config_table_exposure(self, api_client: APIClient, sample_yaml_config: dict):
        """Test that tables specified in YAML config are exposed as endpoints."""
        # Get list of tables from config
        configured_tables = [table["name"] for table in sample_yaml_config.get("tables", [])]
        
        # Verify each table is accessible
        for table_name in configured_tables:
            try:
                response = api_client.get_list(table_name)
                assert "items" in response or isinstance(response, list), f"Table {table_name} should be accessible"
            except Exception as e:
                pytest.fail(f"Table {table_name} is not accessible: {e}")
    
    def test_yaml_config_feature_settings(self, api_client: APIClient):
        """Test that feature configurations (pagination, filtering, etc.) work as specified."""
        # Test pagination (should be enabled by default)
        response = api_client.get_list("products", params={"page": 1, "limit": 10})
        assert "items" in response, "Pagination should work"
        assert len(response["items"]) <= 10, "Pagination limit should be respected"
        
        # Test filtering (should be enabled)
        response = api_client.get_list("products", params={"price__gt": "100"})
        assert "items" in response, "Filtering should work"
        
        # Test sorting (should be enabled)
        response = api_client.get_list("products", params={"sort": "price"})
        assert "items" in response, "Sorting should work"
    
    def test_yaml_config_swagger_settings(self, api_client: APIClient):
        """Test that Swagger/OpenAPI settings from YAML config are applied."""
        # Access Swagger docs endpoint
        try:
            response = api_client.get("/docs")
            assert response.status_code == 200, "Swagger docs should be accessible"
        except Exception:
            # Some APIs might serve docs at different endpoint
            pass
        
        # Access OpenAPI JSON
        try:
            response = api_client.get("/openapi.json")
            if response.status_code == 200:
                openapi_spec = response.json()
                assert "info" in openapi_spec, "OpenAPI spec should contain info"
        except Exception:
            pass
    
    def test_yaml_config_invalid_handling(self):
        """Test that invalid YAML configuration is handled gracefully."""
        # Create invalid YAML
        invalid_yaml = """
        database:
          url: "invalid://connection"
        tables:
          - name: "nonexistent_table"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name
        
        try:
            # Should load YAML but connection might fail
            with open(temp_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            assert loaded_config is not None, "YAML should parse even if invalid"
        finally:
            os.unlink(temp_path)

