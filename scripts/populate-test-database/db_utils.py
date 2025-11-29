"""Database connection utilities for PostgreSQL."""

from urllib.parse import urlparse

import psycopg2

from .exceptions import ConnectionError


def parse_connection_string(connection_string: str) -> dict[str, str]:
    """Parse PostgreSQL connection string into components.

    Args:
        connection_string: PostgreSQL connection URL

    Returns:
        Dictionary with connection components (scheme, user, password, host, port, database)

    Raises:
        ConnectionError: If connection string format is invalid
    """
    if not connection_string or not isinstance(connection_string, str):
        raise ConnectionError("Connection string must be a non-empty string", connection_string)

    try:
        parsed = urlparse(connection_string)
    except Exception as e:
        raise ConnectionError(f"Invalid connection string format: {e}", connection_string) from e

    if not parsed.scheme:
        raise ConnectionError(
            "Connection string must start with 'postgresql://' or 'postgres://'",
            connection_string,
        )

    scheme = parsed.scheme.lower()
    if scheme not in ("postgresql", "postgres"):
        raise ConnectionError(
            f"Invalid scheme '{scheme}'. Must be 'postgresql' or 'postgres'",
            connection_string,
        )

    if not parsed.netloc:
        raise ConnectionError("Connection string must include host", connection_string)

    if not parsed.path or parsed.path == "/":
        raise ConnectionError("Connection string must include database name", connection_string)

    return {
        "scheme": scheme,
        "user": parsed.username or "",
        "password": parsed.password or "",
        "host": parsed.hostname or "",
        "port": str(parsed.port) if parsed.port else "5432",
        "database": parsed.path.lstrip("/"),
    }


def validate_connection(connection_string: str) -> bool:
    """Validate database connection.

    Args:
        connection_string: PostgreSQL connection URL

    Returns:
        True if connection is valid, False otherwise

    Raises:
        ConnectionError: If connection fails with detailed error message
    """
    try:
        conn = psycopg2.connect(connection_string)
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        # Mask password in connection string for error message
        masked_url = _mask_password(connection_string)
        raise ConnectionError(
            f"Failed to connect to database: {e}",
            masked_url,
        ) from e
    except Exception as e:
        masked_url = _mask_password(connection_string)
        raise ConnectionError(
            f"Unexpected error connecting to database: {e}",
            masked_url,
        ) from e


def _mask_password(connection_string: str) -> str:
    """Mask password in connection string for error messages.

    Args:
        connection_string: Original connection string

    Returns:
        Connection string with password masked
    """
    try:
        parsed = urlparse(connection_string)
        if parsed.password:
            # Replace password with ***
            netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
            new_parsed = parsed._replace(netloc=netloc)
            return new_parsed.geturl()
        return connection_string
    except Exception:
        # If parsing fails, return as-is
        return connection_string
