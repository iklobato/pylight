"""Database reflection engine."""

from typing import Any, Dict, List, Type
from sqlalchemy import inspect, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from src.domain.entities.rest_endpoint import RestEndpoint, Base
from src.domain.errors import ReflectionError
from src.infrastructure.database.connection import DatabaseManager


class DatabaseReflection:
    """Reflects database schema and generates models."""

    def __init__(self, databaseUrl: str) -> None:
        """Initialize database reflection.

        Args:
            databaseUrl: Database connection URL
        """
        self.databaseUrl = databaseUrl
        self.databaseManager = DatabaseManager(databaseUrl, asyncMode=False)

    def reflectTables(self) -> List[str]:
        """Discover all tables in the database.

        Returns:
            List of table names

        Raises:
            ReflectionError: If reflection fails
        """
        try:
            inspector = inspect(self.databaseManager.engine)
            return inspector.get_table_names()
        except Exception as e:
            raise ReflectionError(f"Failed to reflect tables: {e}") from e

    def reflectTable(self, tableName: str) -> Dict[str, Any]:
        """Reflect a single table's structure.

        Args:
            tableName: Name of the table to reflect

        Returns:
            Dictionary with table structure information
        """
        try:
            inspector = inspect(self.databaseManager.engine)
            columns = inspector.get_columns(tableName)
            foreignKeys = inspector.get_foreign_keys(tableName)
            indexes = inspector.get_indexes(tableName)
            primaryKey = inspector.get_pk_constraint(tableName)

            return {
                "name": tableName,
                "columns": columns,
                "foreign_keys": foreignKeys,
                "indexes": indexes,
                "primary_key": primaryKey,
            }
        except Exception as e:
            raise ReflectionError(f"Failed to reflect table {tableName}: {e}") from e

    def reflectRelationships(self, tableName: str) -> List[Dict[str, Any]]:
        """Discover relationships for a table.

        Args:
            tableName: Name of the table

        Returns:
            List of relationship dictionaries
        """
        try:
            inspector = inspect(self.databaseManager.engine)
            foreignKeys = inspector.get_foreign_keys(tableName)
            relationships = []

            for fk in foreignKeys:
                relationships.append(
                    {
                        "local_column": fk["constrained_columns"][0],
                        "remote_table": fk["referred_table"],
                        "remote_column": fk["referred_columns"][0],
                    }
                )

            return relationships
        except Exception as e:
            raise ReflectionError(f"Failed to reflect relationships for {tableName}: {e}") from e

