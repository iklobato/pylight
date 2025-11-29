"""CLI entry point."""

from . import click_compat as click
from cli.commands.init import initCommand
from cli.commands.migrate import migrateCommand
from cli.commands.generate import generateCommand
from cli.commands.reflect import reflectCommand
from cli.commands.start import startCommand

# Import populate-test-database command (optional, may not be available in all installations)
populate_test_database = None
try:
    import sys
    import importlib.util
    from pathlib import Path

    # Add project root to path if scripts directory exists
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / "scripts" / "populate-test-database"
    cli_file = scripts_dir / "cli.py"

    if cli_file.exists():
        # Add scripts parent to path for relative imports
        if str(scripts_dir.parent) not in sys.path:
            sys.path.insert(0, str(scripts_dir.parent))
        # Load module using importlib to handle hyphenated directory
        spec = importlib.util.spec_from_file_location(
            "populate_test_database_cli", cli_file
        )
        if spec and spec.loader:
            # Create a mock module for the parent to enable relative imports
            import types

            populate_test_database_module = types.ModuleType("populate_test_database")
            populate_test_database_module.__path__ = [str(scripts_dir)]
            sys.modules["populate_test_database"] = populate_test_database_module

            # Load the CLI module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            populate_test_database = getattr(module, "populate_test_database", None)
except Exception as e:
    # Silently fail if command is not available
    # Uncomment for debugging:
    # import traceback
    # traceback.print_exc()
    populate_test_database = None


@click.group()
def main() -> None:
    """Pylight CLI - Next-generation Python API framework."""
    pass


main.add_command(initCommand)
main.add_command(migrateCommand)
main.add_command(generateCommand)
main.add_command(reflectCommand)
main.add_command(startCommand)

# Add populate-test-database command if available
if populate_test_database is not None:
    main.add_command(populate_test_database)


if __name__ == "__main__":
    main()
