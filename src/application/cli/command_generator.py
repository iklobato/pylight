"""CLI command generator."""

from typing import Any, Type
import click

from src.domain.entities.rest_endpoint import RestEndpoint


class CLICommandGenerator:
    """Generates CLI commands from RestEndpoint models."""

    @staticmethod
    def generateCommands(model: Type[RestEndpoint]) -> list[click.Command]:
        """Generate CLI commands for a model.

        Args:
            model: Model class

        Returns:
            List of Click command objects
        """
        tableName = model.getTableName()

        @click.command(name=f"{tableName}:list")
        def listCommand():
            """List all {tableName} records."""
            click.echo(f"Listing {tableName} - Implementation pending")

        @click.command(name=f"{tableName}:create")
        def createCommand():
            """Create a new {tableName} record."""
            click.echo(f"Creating {tableName} - Implementation pending")

        return [listCommand, createCommand]

