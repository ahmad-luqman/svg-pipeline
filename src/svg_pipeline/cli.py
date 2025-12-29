"""Command-line interface for SVG Pipeline."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from svg_pipeline import __version__
from svg_pipeline.pipeline import Pipeline
from svg_pipeline.presets import list_presets
from svg_pipeline.templates import TEMPLATES_DIR, get_template

app = typer.Typer(
    name="svg-pipeline",
    help="Transform SVG sources into all required derivative formats.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"svg-pipeline version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """SVG Pipeline - Transform SVG sources into deployment-ready assets."""
    pass


@app.command()
def generate(
    source: Annotated[Path, typer.Argument(help="Source SVG or image file")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Output directory")
    ] = Path("./output"),
    preset: Annotated[
        Optional[str], typer.Option("--preset", "-p", help="Preset to use (web, mobile, full)")
    ] = None,
    background: Annotated[
        Optional[str], typer.Option("--bg", help="Background color (hex, e.g., '#282a36')")
    ] = None,
    foreground: Annotated[
        Optional[str], typer.Option("--fg", help="Foreground color (hex, e.g., '#f8f8f2')")
    ] = None,
    fit: Annotated[
        str, typer.Option("--fit", "-f", help="Fit mode: cover (crop), contain (pad), stretch")
    ] = "cover",
    parallel: Annotated[
        bool, typer.Option("--parallel", "-P", help="Enable parallel processing")
    ] = False,
    workers: Annotated[
        Optional[int], typer.Option("--workers", "-w", help="Number of parallel workers")
    ] = None,
) -> None:
    """Generate assets from a source SVG or image file."""
    try:
        if not source.exists():
            console.print(f"[red]Error:[/red] Source file not found: {source}")
            raise typer.Exit(1)

        pipeline = Pipeline(source)

        if preset:
            pipeline.with_preset(preset)
        else:
            # Default to web preset if none specified
            pipeline.with_preset("web")

        if background or foreground:
            pipeline.with_colors(foreground=foreground, background=background)

        if parallel:
            pipeline.with_parallel(max_workers=workers)

        pipeline.with_fit_mode(fit)

        status_msg = "[bold green]Generating assets"
        if parallel:
            status_msg += " (parallel)"
        status_msg += "...[/bold green]"

        with console.status(status_msg):
            generated = pipeline.generate(output)

        console.print(f"\n[green]✓[/green] Generated {len(generated)} files to {output}/\n")

        # Show generated files
        table = Table(show_header=True, header_style="bold")
        table.add_column("File")
        table.add_column("Size", justify="right")

        for path in sorted(generated):
            if path.exists():
                size = path.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                table.add_row(path.name, size_str)

        console.print(table)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def template(
    name: Annotated[str, typer.Argument(help="Template name (e.g., 'silhouette')")],
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Output directory")
    ] = Path("./output"),
    background: Annotated[
        Optional[str], typer.Option("--bg", help="Background color (hex)")
    ] = None,
    foreground: Annotated[
        Optional[str], typer.Option("--fg", help="Foreground color (hex)")
    ] = None,
    preset: Annotated[
        Optional[str], typer.Option("--preset", "-p", help="Preset to use")
    ] = "web",
    parallel: Annotated[
        bool, typer.Option("--parallel", "-P", help="Enable parallel processing")
    ] = False,
) -> None:
    """Generate assets from a built-in template."""
    try:
        template_path = get_template(name)

        pipeline = Pipeline(template_path)

        if preset:
            pipeline.with_preset(preset)

        if background or foreground:
            pipeline.with_colors(foreground=foreground, background=background)

        if parallel:
            pipeline.with_parallel()

        with console.status("[bold green]Generating from template...[/bold green]"):
            generated = pipeline.generate(output)

        console.print(
            f"\n[green]✓[/green] Generated {len(generated)} files from '{name}' template\n"
        )

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("list-presets")
def list_presets_cmd() -> None:
    """List available presets."""
    presets = list_presets()

    console.print("\n[bold]Available Presets:[/bold]\n")
    for preset in presets:
        console.print(f"  • {preset}")
    console.print()


@app.command("list-templates")
def list_templates_cmd() -> None:
    """List available built-in templates."""
    templates = [p.stem for p in TEMPLATES_DIR.glob("*.svg")]

    console.print("\n[bold]Available Templates:[/bold]\n")
    if templates:
        for template in templates:
            console.print(f"  • {template}")
    else:
        console.print("  (no templates installed)")
    console.print()


if __name__ == "__main__":
    app()
