"""CLI start command for YAML-driven API startup."""

import os
from cli import click_compat as click

from src.presentation.app import LightApi
from src.domain.errors import ConfigurationError, ReflectionError


@click.command("start")
@click.option("--config", type=str, help="Path to YAML configuration file")
@click.option("--host", type=str, default="127.0.0.1", help="Server host")
@click.option("--port", type=int, default=8000, help="Server port")
def startCommand(config: str, host: str, port: int) -> None:
    """Start Pylight server from YAML configuration.

    Args:
        config: Path to YAML configuration file (or from PYLIGHT_CONFIG env var)
        host: Server host
        port: Server port
    """
    yamlPath = config or os.getenv("PYLIGHT_CONFIG")

    if not yamlPath:
        click.echo("Error: YAML configuration file path required.", err=True)
        click.echo("  Use --config <path> or set PYLIGHT_CONFIG environment variable", err=True)
        click.echo("  Example: pylight start --config api-config.yaml", err=True)
        raise click.Abort()

    if not os.path.exists(yamlPath):
        click.echo(f"Error: Configuration file not found: {yamlPath}", err=True)
        raise click.Abort()

    try:
        click.echo(f"Loading configuration from: {yamlPath}")
        app = LightApi.fromYamlConfig(yamlPath)
        click.echo("✓ Configuration loaded successfully")
        click.echo(f"✓ Registered {len(app.registeredModels)} table(s)")
        click.echo(f"Starting server on http://{host}:{port}")
        click.echo(f"API documentation: http://{host}:{port}/docs")
        app.run(host=host, port=port)
    except ConfigurationError as e:
        click.echo(f"Configuration error: {e}", err=True)
        raise click.Abort()
    except ReflectionError as e:
        click.echo(f"Database reflection error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)
        raise click.Abort()
