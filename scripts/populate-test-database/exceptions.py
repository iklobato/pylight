"""Custom exception classes for database population routine."""


class ConnectionError(Exception):
    """Raised when database connection fails."""

    def __init__(self, message: str, connection_string: str) -> None:
        """Initialize connection error.

        Args:
            message: Error message
            connection_string: Connection string that failed (password will be masked)
        """
        super().__init__(message)
        self.message = message
        self.connection_string = connection_string


class SchemaError(Exception):
    """Raised when schema operations fail."""

    def __init__(self, message: str, sql_statement: str | None = None) -> None:
        """Initialize schema error.

        Args:
            message: Error message
            sql_statement: SQL statement that failed (optional)
        """
        super().__init__(message)
        self.message = message
        self.sql_statement = sql_statement


class DataGenerationError(Exception):
    """Raised when data generation fails."""

    def __init__(
        self,
        message: str,
        table_name: str | None = None,
        record_number: int | None = None,
    ) -> None:
        """Initialize data generation error.

        Args:
            message: Error message
            table_name: Name of table where error occurred (optional)
            record_number: Record number where error occurred (optional)
        """
        super().__init__(message)
        self.message = message
        self.table_name = table_name
        self.record_number = record_number


class TableNotFoundError(Exception):
    """Raised when table doesn't exist."""

    def __init__(self, table_name: str) -> None:
        """Initialize table not found error.

        Args:
            table_name: Name of table that doesn't exist
        """
        super().__init__(f"Table '{table_name}' not found")
        self.table_name = table_name


class CircularDependencyError(Exception):
    """Raised when circular dependencies detected in table relationships."""

    def __init__(self, cycle: list[str]) -> None:
        """Initialize circular dependency error.

        Args:
            cycle: List of table names forming the cycle
        """
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")
        self.cycle = cycle
