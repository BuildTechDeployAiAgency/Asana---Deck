"""CLI entry point — the `asana-deck` command."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from asana_deck.config import Config
from asana_deck.asana_client import AsanaClient
from asana_deck.ai_processor import AIProcessor
from asana_deck.generators.pptx_generator import PptxGenerator

console = Console()


@click.command()
@click.argument("project_gid")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["pptx", "google_slides"]),
    default=None,
    help="Output format (default: from .env or pptx).",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output file path (for pptx) or ignored for Google Slides.",
)
@click.option(
    "--project-name",
    default=None,
    help="Human-readable project name for the deck title.",
)
@click.option(
    "--include-completed",
    is_flag=True,
    default=False,
    help="Include completed tasks in the deck.",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    default=None,
    help="Path to .env file (default: .env in cwd).",
)
@click.option(
    "--model",
    default="claude-sonnet-4-20250514",
    help="Claude model to use for AI processing.",
)
def main(
    project_gid: str,
    output_format: str | None,
    output: str | None,
    project_name: str | None,
    include_completed: bool,
    env_file: str | None,
    model: str,
) -> None:
    """Generate a slide deck from an Asana project board.

    PROJECT_GID is the Asana project ID (found in the project URL).
    """
    # ── Load config ───────────────────────────────────────────────────
    config = Config.from_env(env_file)
    if output_format:
        config.output_format = output_format

    errors = config.validate()
    if errors:
        for err in errors:
            console.print(f"[red]Error:[/red] {err}")
        sys.exit(1)

    # ── Fetch from Asana ──────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Connecting to Asana...", total=None)
        asana_client = AsanaClient(config.asana_access_token)

        progress.update(task, description="Fetching tasks by section...")
        tasks_by_section = asana_client.get_tasks_by_section(
            project_gid, include_completed=include_completed
        )

    total_tasks = sum(len(t) for t in tasks_by_section.values())
    sections = list(tasks_by_section.keys())
    console.print(
        f"[green]Fetched {total_tasks} tasks across {len(sections)} sections.[/green]"
    )

    if total_tasks == 0:
        console.print("[yellow]No tasks found — nothing to generate.[/yellow]")
        sys.exit(0)

    name = project_name or f"Asana Project {project_gid}"

    # ── AI processing ─────────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing with AI...", total=None)
        processor = AIProcessor(config.anthropic_api_key, model=model)

        progress.update(task, description="Building deck structure...")
        deck = processor.build_deck(name, tasks_by_section)

    console.print(
        f"[green]AI generated {len(deck.slides)} slides.[/green]"
    )

    # ── Generate output ───────────────────────────────────────────────
    if config.output_format == "pptx":
        if output is None:
            config.output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = str(config.output_dir / f"deck_{timestamp}.pptx")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating PowerPoint...", total=None)
            generator = PptxGenerator(config)
            path = generator.generate(deck, output)

        console.print(f"[bold green]Deck saved to:[/bold green] {path}")

    elif config.output_format == "google_slides":
        from asana_deck.generators.google_slides_generator import (
            GoogleSlidesGenerator,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Creating Google Slides presentation...", total=None
            )
            generator = GoogleSlidesGenerator(config)
            url = generator.generate(deck)

        console.print(f"[bold green]Presentation created:[/bold green] {url}")


if __name__ == "__main__":
    main()
