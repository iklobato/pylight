"""Configuration data class for data generation."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DataGenerationConfig:
    """Configuration for test data generation.

    Attributes:
        connection_string: PostgreSQL connection string (or use DATABASE_URL env var)
        schema_creation_enabled: Whether to create/drop schema
        seed: Seed value for reproducibility (optional, or use PYLIGHT_POPULATE_SEED env var)
        record_counts: Record counts per table (table_name -> count)
        cleanup_on_failure: Whether to clean up partial data on failure
    """

    connection_string: Optional[str] = None
    schema_creation_enabled: bool = False
    seed: Optional[int] = None
    record_counts: dict[str, int] = field(default_factory=dict)
    cleanup_on_failure: bool = True

    def __post_init__(self) -> None:
        """Initialize configuration from environment variables if not provided."""
        # Get connection string from environment if not provided
        if self.connection_string is None:
            self.connection_string = os.getenv("DATABASE_URL")
            if self.connection_string is None:
                raise ValueError(
                    "connection_string must be provided or DATABASE_URL environment variable must be set"
                )

        # Get seed from environment if not provided
        if self.seed is None:
            seed_env = os.getenv("PYLIGHT_POPULATE_SEED")
            if seed_env:
                try:
                    self.seed = int(seed_env)
                except ValueError:
                    pass  # Ignore invalid seed values

    def get_record_count(self, table_name: str, default: int = 1000) -> int:
        """Get record count for a table.

        Args:
            table_name: Name of table
            default: Default count if not specified

        Returns:
            Record count for the table
        """
        return self.record_counts.get(table_name, default)
