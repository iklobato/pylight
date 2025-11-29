"""CLI command for populating test database."""

import json
import os
import sys
import importlib.util
from pathlib import Path

import click

# Load modules directly from files (workaround for hyphenated directory)
_current_dir = Path(__file__).parent

# Set up module structure first
import types

_populate_test_db_module = types.ModuleType("populate_test_database")
_populate_test_db_module.__path__ = [str(_current_dir)]
sys.modules["populate_test_database"] = _populate_test_db_module

# Load exceptions FIRST (needed by other modules)
_exceptions_spec = importlib.util.spec_from_file_location(
    "populate_test_database.exceptions", _current_dir / "exceptions.py"
)
exceptions_module = importlib.util.module_from_spec(_exceptions_spec)
exceptions_module.__package__ = "populate_test_database"
sys.modules["populate_test_database.exceptions"] = exceptions_module
_exceptions_spec.loader.exec_module(exceptions_module)
ConnectionError = exceptions_module.ConnectionError
DataGenerationError = exceptions_module.DataGenerationError
SchemaError = exceptions_module.SchemaError

# Load config
_config_spec = importlib.util.spec_from_file_location(
    "populate_test_database.config", _current_dir / "config.py"
)
config_module = importlib.util.module_from_spec(_config_spec)
config_module.__package__ = "populate_test_database"
sys.modules["populate_test_database.config"] = config_module
_config_spec.loader.exec_module(config_module)
DataGenerationConfig = config_module.DataGenerationConfig

# Load db_utils (needed by data_generator and schema_generator)
_db_utils_spec = importlib.util.spec_from_file_location(
    "populate_test_database.db_utils", _current_dir / "db_utils.py"
)
db_utils_module = importlib.util.module_from_spec(_db_utils_spec)
db_utils_module.__package__ = "populate_test_database"
sys.modules["populate_test_database.db_utils"] = db_utils_module
_db_utils_spec.loader.exec_module(db_utils_module)

# Load dependency_resolver (needed by data_generator)
_dep_resolver_spec = importlib.util.spec_from_file_location(
    "populate_test_database.dependency_resolver", _current_dir / "dependency_resolver.py"
)
dep_resolver_module = importlib.util.module_from_spec(_dep_resolver_spec)
dep_resolver_module.__package__ = "populate_test_database"
sys.modules["populate_test_database.dependency_resolver"] = dep_resolver_module
_dep_resolver_spec.loader.exec_module(dep_resolver_module)

# Load data_generator
_data_gen_spec = importlib.util.spec_from_file_location(
    "populate_test_database.data_generator", _current_dir / "data_generator.py"
)
data_gen_module = importlib.util.module_from_spec(_data_gen_spec)
data_gen_module.__package__ = "populate_test_database"
sys.modules["populate_test_database.data_generator"] = data_gen_module
_data_gen_spec.loader.exec_module(data_gen_module)
DataGenerator = data_gen_module.DataGenerator


# Load schema_generator
_schema_spec = importlib.util.spec_from_file_location(
    "populate_test_database.schema_generator", _current_dir / "schema_generator.py"
)
schema_module = importlib.util.module_from_spec(_schema_spec)
schema_module.__package__ = "populate_test_database"
sys.modules["populate_test_database.schema_generator"] = schema_module
_schema_spec.loader.exec_module(schema_module)
SchemaGenerator = schema_module.SchemaGenerator

# Load utils
_utils_spec = importlib.util.spec_from_file_location(
    "populate_test_database.utils", _current_dir / "utils.py"
)
utils_module = importlib.util.module_from_spec(_utils_spec)
utils_module.__package__ = "populate_test_database"
sys.modules["populate_test_database.utils"] = utils_module
_utils_spec.loader.exec_module(utils_module)
log_error = utils_module.log_error
log_success = utils_module.log_success
setup_logging = utils_module.setup_logging


@click.command(name="populate-test-database")
@click.option(
    "--connection-string",
    "-c",
    default=None,
    help="PostgreSQL connection string (or use DATABASE_URL env var)",
)
@click.option(
    "--create-schema",
    "-s",
    is_flag=True,
    default=False,
    help="Create/drop schema before populating",
)
@click.option(
    "--seed",
    "-S",
    type=int,
    default=None,
    help="Seed value for reproducibility",
)
@click.option(
    "--records-per-table",
    "-r",
    type=int,
    default=1000,
    help="Default number of records per table",
)
@click.option(
    "--table-counts",
    "-t",
    type=str,
    default=None,
    help="JSON dict of table-specific record counts (e.g., '{\"users\": 2000, \"products\": 5000}')",
)
@click.option(
    "--cleanup-on-failure",
    "-C",
    is_flag=True,
    default=True,
    help="Clean up partial data on failure",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress non-error output")
def populate_test_database(
    connection_string: str,
    create_schema: bool,
    seed: int,
    records_per_table: int,
    table_counts: str,
    cleanup_on_failure: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """Populate PostgreSQL database with realistic test data for Pylight feature testing.

    This command generates an e-commerce schema with 10+ interconnected tables
    and populates them with realistic test data using Faker.
    """
    setup_logging(verbose=verbose, quiet=quiet)

    # Get connection string
    conn_str = connection_string or os.getenv("DATABASE_URL")
    if not conn_str:
        log_error("Connection string required. Use --connection-string or set DATABASE_URL")
        sys.exit(1)

    # Parse table counts
    table_counts_dict = {}
    if table_counts:
        try:
            table_counts_dict = json.loads(table_counts)
        except json.JSONDecodeError:
            log_error(f"Invalid JSON in --table-counts: {table_counts}")
            sys.exit(1)

    try:
        # Create schema if requested
        if create_schema:
            log_success("Creating schema...")
            schema_gen = SchemaGenerator(conn_str)
            schema_gen.create_schema(drop_existing=True)
            log_success("Schema created successfully")

        # Generate data
        config = DataGenerationConfig(
            connection_string=conn_str,
            schema_creation_enabled=False,  # Already created if --create-schema
            seed=seed,
            record_counts=table_counts_dict,
            cleanup_on_failure=cleanup_on_failure,
        )

        # Set default record count
        if not table_counts_dict:
            for table_name in [
                "users",
                "categories",
                "products",
                "addresses",
                "orders",
                "order_items",
                "reviews",
                "payments",
                "shipments",
                "inventory",
            ]:
                config.record_counts[table_name] = records_per_table

        generator = DataGenerator(config)
        counts = generator.generate_all()

        # Print summary
        total = sum(counts.values())
        log_success(f"Data generation complete: {total} total records")
        if verbose:
            for table, count in counts.items():
                log_success(f"  {table}: {count} records")

    except ConnectionError as e:
        log_error(f"Database connection failed: {e}")
        sys.exit(1)
    except SchemaError as e:
        log_error(f"Schema operation failed: {e}")
        sys.exit(1)
    except DataGenerationError as e:
        log_error(f"Data generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)
