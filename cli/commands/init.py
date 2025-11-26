"""CLI init command to scaffold new projects."""

import os
import shutil
from pathlib import Path
import click_compat as click


@click.command("init")
@click.argument("project_name", type=str)
def initCommand(projectName: str) -> None:
    """Initialize a new Pylight project.

    Args:
        projectName: Name of the project to create
    """
    projectPath = Path(projectName)
    if projectPath.exists():
        click.echo(f"Error: Directory '{projectName}' already exists", err=True)
        return

    try:
        projectPath.mkdir(parents=True, exist_ok=True)
        templateDir = Path(__file__).parent.parent / "templates" / "project"

        if templateDir.exists():
            for item in templateDir.rglob("*"):
                if item.is_file():
                    relativePath = item.relative_to(templateDir)
                    targetPath = projectPath / relativePath
                    targetPath.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, targetPath)

        click.echo(f"✓ Created project '{projectName}'")
        click.echo(f"  cd {projectName}")
        click.echo("  python main.py")
    except Exception as e:
        click.echo(f"Error creating project: {e}", err=True)
        if projectPath.exists():
            shutil.rmtree(projectPath)

