"""Database connection utilities for tests."""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
import time


class DatabaseClient:
    """Client for database operations in tests."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None
    
    def connect(self, retries: int = 5, delay: int = 2) -> bool:
        """Establish database connection with retry logic."""
        for attempt in range(retries):
            try:
                self.conn = psycopg2.connect(
                    self.connection_string,
                    connect_timeout=2
                )
                self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                return True
            except psycopg2.OperationalError as e:
                if attempt < retries - 1:
                    print(f"Connection attempt {attempt + 1} failed, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"Failed to connect after {retries} attempts: {e}")
                    return False
        return False
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dictionaries."""
        if not self.cursor:
            raise RuntimeError("Database not connected")
        
        self.cursor.execute(query, params or ())
        return self.cursor.fetchall()
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows."""
        if not self.cursor:
            raise RuntimeError("Database not connected")
        
        self.cursor.execute(query, params or ())
        self.conn.commit()
        return self.cursor.rowcount
    
    def get_table_count(self, table_name: str) -> int:
        """Get total record count for a table."""
        result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        return result[0]['count'] if result else 0
    
    def get_table_record(self, table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Get a single record by ID."""
        result = self.execute_query(
            f"SELECT * FROM {table_name} WHERE id = %s",
            (record_id,)
        )
        return result[0] if result else None
    
    def verify_record_exists(self, table_name: str, record_id: int) -> bool:
        """Verify a record exists in the table."""
        record = self.get_table_record(table_name, record_id)
        return record is not None
    
    def verify_record_deleted(self, table_name: str, record_id: int) -> bool:
        """Verify a record has been deleted from the table."""
        record = self.get_table_record(table_name, record_id)
        return record is None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

