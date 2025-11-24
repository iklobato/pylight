"""Model code generation from database reflection."""

from typing import Any, Dict, List
from pathlib import Path

from src.infrastructure.database.reflection import DatabaseReflection


class ModelGenerator:
    """Generates model code from reflected database schema."""

    def __init__(self, reflection: DatabaseReflection) -> None:
        """Initialize model generator.

        Args:
            reflection: DatabaseReflection instance
        """
        self.reflection = reflection

    def generateModelCode(self, tableInfo: Dict[str, Any]) -> str:
        """Generate Python code for a model from table information.

        Args:
            tableInfo: Table structure information from reflection

        Returns:
            Python code string for the model class
        """
        tableName = tableInfo["name"]
        className = self._toPascalCase(tableName)
        columns = tableInfo["columns"]
        foreignKeys = tableInfo["foreign_keys"]

        code = f'''"""Generated model for {tableName} table."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from src.domain.entities.rest_endpoint import RestEndpoint


class {className}(RestEndpoint):
    """Model for {tableName} table."""

    __tablename__ = "{tableName}"

'''
        for col in columns:
            colName = col["name"]
            colType = self._mapColumnType(col["type"])
            nullable = col.get("nullable", True)
            default = col.get("default")
            primaryKey = colName in tableInfo["primary_key"].get("constrained_columns", [])

            colDef = f"    {colName} = Column({colType}"
            if not nullable:
                colDef += ", nullable=False"
            if primaryKey:
                colDef += ", primary_key=True"
            if default:
                colDef += f", default={default}"
            colDef += ")\n"

            code += colDef

        for fk in foreignKeys:
            localCol = fk["constrained_columns"][0]
            remoteTable = fk["referred_table"]
            remoteCol = fk["referred_columns"][0]
            code += f'\n    # Foreign key: {localCol} -> {remoteTable}.{remoteCol}\n'

        return code

    def _toPascalCase(self, snakeStr: str) -> str:
        """Convert snake_case to PascalCase."""
        components = snakeStr.split("_")
        return "".join(word.capitalize() for word in components)

    def _mapColumnType(self, sqlType: Any) -> str:
        """Map SQLAlchemy column type to string representation."""
        typeStr = str(sqlType).lower()
        if "int" in typeStr:
            return "Integer"
        elif "varchar" in typeStr or "text" in typeStr or "string" in typeStr:
            return "String"
        elif "datetime" in typeStr or "timestamp" in typeStr:
            return "DateTime"
        elif "bool" in typeStr:
            return "Boolean"
        elif "float" in typeStr or "decimal" in typeStr:
            return "Float"
        else:
            return "String"

