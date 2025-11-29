"""Tests for database utilities."""

import pytest

from scripts.populate_test_database.db_utils import parse_connection_string, validate_connection
from scripts.populate_test_database.exceptions import ConnectionError


def test_parse_connection_string():
    """Test connection string parsing."""
    # Valid connection string
    conn_str = "postgresql://user:password@localhost:5432/dbname"
    parsed = parse_connection_string(conn_str)

    assert parsed["scheme"] == "postgresql"
    assert parsed["user"] == "user"
    assert parsed["password"] == "password"
    assert parsed["host"] == "localhost"
    assert parsed["port"] == "5432"
    assert parsed["database"] == "dbname"


def test_parse_connection_string_invalid_scheme():
    """Test that invalid scheme raises error."""
    with pytest.raises(ConnectionError):
        parse_connection_string("mysql://user:pass@localhost/db")


def test_parse_connection_string_missing_host():
    """Test that missing host raises error."""
    with pytest.raises(ConnectionError):
        parse_connection_string("postgresql:///dbname")


def test_parse_connection_string_missing_database():
    """Test that missing database raises error."""
    with pytest.raises(ConnectionError):
        parse_connection_string("postgresql://user:pass@localhost/")


def test_validate_connection(test_connection_string):
    """Test connection validation with valid connection."""
    # This test requires a running PostgreSQL instance
    # Skip if connection fails
    try:
        result = validate_connection(test_connection_string)
        assert result is True
    except ConnectionError:
        pytest.skip("PostgreSQL not available for testing")


def test_validate_connection_invalid():
    """Test connection validation with invalid connection."""
    invalid_conn = "postgresql://invalid:invalid@localhost:5432/nonexistent"
    with pytest.raises(ConnectionError):
        validate_connection(invalid_conn)


def test_connection_error_handling():
    """Test that connection errors provide clear messages."""
    invalid_conn = "postgresql://user:pass@nonexistent:5432/db"
    try:
        validate_connection(invalid_conn)
        pytest.skip("Connection unexpectedly succeeded")
    except ConnectionError as e:
        assert "Failed to connect" in str(e)
        assert "nonexistent" in e.connection_string
        # Password should be masked
        assert "pass" not in e.connection_string or "***" in e.connection_string
