"""CLI entry point."""

from . import click_compat as click
from cli.commands.init import initCommand
from cli.commands.migrate import migrateCommand
from cli.commands.generate import generateCommand
from cli.commands.reflect import reflectCommand
from cli.commands.start import startCommand


@click.group()
def main() -> None:
    """Pylight CLI - Next-generation Python API framework."""
    pass


main.add_command(initCommand)
main.add_command(migrateCommand)
main.add_command(generateCommand)
main.add_command(reflectCommand)
main.add_command(startCommand)


if __name__ == "__main__":
    main()

