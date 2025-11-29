"""Database utilities for integration examples."""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine


def create_database_connection(database_url: str) -> Tuple[Engine, sessionmaker]:
    """Create database connection and session factory.

    Args:
        database_url: Database connection URL

    Returns:
        Tuple of (engine, sessionmaker)
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return engine, Session


def verify_database_state(
    session: Session, table_name: str, record_id: Optional[int] = None, test_prefix: str = "test_", **filters
) -> Optional[Dict[str, Any]] | List[Dict[str, Any]]:
    """Query database and validate state.

    Args:
        session: Database session
        table_name: Table name to query
        record_id: Optional record ID to query
        test_prefix: Prefix for test data filtering (used when record_id is None)
        **filters: Additional filter criteria

    Returns:
        Record as dictionary or None if not found (when record_id provided),
        or list of records (when record_id is None)
    """
    if record_id is not None:
        query = text(f"SELECT * FROM {table_name} WHERE id = :id")
        result = session.execute(query, {"id": record_id})
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None

    # Build query with filters
    query = f"SELECT * FROM {table_name}"
    params = {}
    conditions = []
    
    # Add test prefix filter if name column exists
    if test_prefix:
        conditions.append("name LIKE :test_prefix")
        params["test_prefix"] = f"{test_prefix}%"
    
    if filters:
        for key, value in filters.items():
            conditions.append(f"{key} = :{key}")
            params[key] = value
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    result = session.execute(text(query), params)
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows] if rows else []


def cleanup_test_data(
    session: Session, table_name: str, test_prefix: str = "test_"
) -> None:
    """Remove test data after examples.

    Args:
        session: Database session
        table_name: Table name to clean
        test_prefix: Prefix to identify test data
    """
    try:
        # Delete records with test prefix in name field (for products)
        query = text(f"DELETE FROM {table_name} WHERE name LIKE :prefix")
        session.execute(query, {"prefix": f"{test_prefix}%"})
        session.commit()
    except Exception as e:
        print(f"WARNING: Error cleaning up test data: {e}")
        session.rollback()


def cleanup_all_test_data(session: Session, tables: List[str], test_prefix: str = "test_") -> None:
    """Remove test data from multiple tables.

    Args:
        session: Database session
        tables: List of table names to clean
        test_prefix: Prefix to identify test data
    """
    for table in tables:
        cleanup_test_data(session, table, test_prefix)

