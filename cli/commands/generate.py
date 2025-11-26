"""CLI generate command for code generation."""

from pathlib import Path
import click_compat as click


@click.command("generate")
@click.argument("model_name", type=str)
@click.option("--output-dir", type=str, default="endpoints", help="Output directory for generated files")
def generateCommand(modelName: str, outputDir: str) -> None:
    """Generate customizable endpoint files from models.

    Args:
        modelName: Name of the model to generate endpoints for
        outputDir: Directory to output generated files
    """
    outputPath = Path(outputDir)
    outputPath.mkdir(parents=True, exist_ok=True)

    endpointFile = outputPath / f"{modelName.lower()}_endpoint.py"
    endpointFile.write_text(
        f'''"""Generated endpoint for {modelName}."""

from src.presentation.rest.get_handler import getHandler
from src.presentation.rest.post_handler import postHandler
from src.presentation.rest.put_handler import putHandler
from src.presentation.rest.delete_handler import deleteHandler
from src.models.{modelName.lower()} import {modelName}

# Customize these handlers as needed
get_{modelName.lower()}_handler = getHandler({modelName})
post_{modelName.lower()}_handler = postHandler({modelName})
put_{modelName.lower()}_handler = putHandler({modelName})
delete_{modelName.lower()}_handler = deleteHandler({modelName})
'''
    )

    click.echo(f"✓ Generated endpoint file: {endpointFile}")
    click.echo(f"  Customize {endpointFile} as needed")

