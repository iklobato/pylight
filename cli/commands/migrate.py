"""CLI migrate command for database schema management."""

import click_compat as click
from src.infrastructure.database.migrations import MigrationManager


@click.command("migrate")
@click.argument("action", type=click.Choice(["create", "upgrade", "downgrade"]))
@click.argument("name", required=False, type=str)
@click.option("--database-url", type=str, help="Database connection URL")
def migrateCommand(action: str, name: str | None, databaseUrl: str | None) -> None:
    """Manage database migrations.

    Args:
        action: Migration action (create, upgrade, downgrade)
        name: Migration name (required for create)
        databaseUrl: Database connection URL
    """
    if action == "create" and not name:
        click.echo("Error: Migration name required for 'create' action", err=True)
        return

    if not databaseUrl:
        click.echo("Error: --database-url required", err=True)
        return

    try:
        migrationManager = MigrationManager(databaseUrl)
        if action == "create":
            migrationManager.createMigration(name)
            click.echo(f"✓ Created migration: {name}")
        elif action == "upgrade":
            migrationManager.upgrade()
            click.echo("✓ Database upgraded")
        elif action == "downgrade":
            if not name:
                click.echo("Error: Revision required for 'downgrade' action", err=True)
                return
            migrationManager.downgrade(name)
            click.echo(f"✓ Database downgraded to: {name}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

