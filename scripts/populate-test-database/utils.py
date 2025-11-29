"""Utility functions for logging and progress reporting."""

import logging
import sys
from typing import Optional

# Configure logging
logger = logging.getLogger("populate_test_database")
logger.setLevel(logging.INFO)

# Create console handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: Enable verbose (DEBUG) logging
        quiet: Suppress all non-error output
    """
    if quiet:
        logger.setLevel(logging.ERROR)
    elif verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def log_progress(table_name: str, current: int, total: int, message: Optional[str] = None) -> None:
    """Log progress for data generation.

    Args:
        table_name: Name of table being populated
        current: Current record number
        total: Total records to generate
        message: Optional additional message
    """
    percentage = (current / total * 100) if total > 0 else 0
    progress_msg = f"→ {table_name}: {current}/{total} records ({percentage:.1f}%)"
    if message:
        progress_msg += f" - {message}"
    logger.info(progress_msg)


def log_success(message: str) -> None:
    """Log success message.

    Args:
        message: Success message
    """
    logger.info(f"✓ {message}")


def log_error(message: str) -> None:
    """Log error message.

    Args:
        message: Error message
    """
    logger.error(f"✗ {message}")
