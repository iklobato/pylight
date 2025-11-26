"""CLI reflect command for database reflection."""

from pathlib import Path
import click_compat as click

from src.infrastructure.database.reflection import DatabaseReflection
from src.infrastructure.database.model_generator import ModelGenerator


@click.command("reflect")
@click.option("--database-url", type=str, required=True, help="Database connection URL")
@click.option("--output-dir", type=str, default="reflected_models", help="Output directory for generated models")
def reflectCommand(databaseUrl: str, outputDir: str) -> None:
    """Reflect database schema and generate models.

    Args:
        databaseUrl: Database connection URL
        outputDir: Directory to output generated model files
    """
    try:
        reflection = DatabaseReflection(databaseUrl)
        tables = reflection.reflectTables()

        click.echo(f"Found {len(tables)} tables in database")

        outputPath = Path(outputDir)
        outputPath.mkdir(parents=True, exist_ok=True)

        generator = ModelGenerator(reflection)

        for tableName in tables:
            tableInfo = reflection.reflectTable(tableName)
            modelCode = generator.generateModelCode(tableInfo)

            modelFile = outputPath / f"{tableName}.py"
            modelFile.write_text(modelCode)
            click.echo(f"✓ Generated model: {modelFile}")

        click.echo(f"\n✓ Reflection complete. Models saved to {outputDir}/")
    except Exception as e:
        click.echo(f"Error during reflection: {e}", err=True)

