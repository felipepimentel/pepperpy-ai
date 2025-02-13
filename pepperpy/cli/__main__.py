"""Main CLI module for Pepperpy.

This module provides the command-line interface for Pepperpy,
including setup, testing, and diagnostics.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from pepperpy import Pepperpy
from pepperpy.cli.setup import setup_wizard

console = Console()


def print_version(ctx: click.Context, _, value: bool) -> None:
    """Print version and exit."""
    if not value or ctx.resilient_parsing:
        return
    from pepperpy import __version__

    console.print(f"Pepperpy version {__version__}")
    ctx.exit()


@click.group()
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show version and exit.",
)
def cli():
    """🌶️ Pepperpy CLI - Your AI research assistant.

    Examples:
        # Initialize Pepperpy:
        $ pepperpy init

        # Quick test:
        $ pepperpy test "How are you?"

        # Run diagnostics:
        $ pepperpy doctor

        # Start interactive chat:
        $ pepperpy chat

        # Run research:
        $ pepperpy research "Impact of AI"

    """
    pass


@cli.command()
def init():
    """🚀 Interactive initialization of Pepperpy.

    This command will guide you through:
    - API key setup
    - Model selection
    - Basic configuration
    - Connection testing
    """
    try:
        asyncio.run(setup_wizard())
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled.[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Setup failed: {e}[/]")
        sys.exit(1)


@cli.command()
@click.argument("message")
@click.option(
    "--style",
    type=click.Choice(["concise", "detailed", "technical"]),
    default="concise",
    help="Response style.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "markdown", "json"]),
    default="text",
    help="Output format.",
)
def test(message: str, style: str, output_format: str):
    """🧪 Quick test of Pepperpy functionality.

    Examples:
        $ pepperpy test "What is AI?"
        $ pepperpy test "Explain quantum computing" --style technical
        $ pepperpy test "Summarize this article" --format markdown

    """

    async def run_test():
        try:
            # Create client
            pepper = await Pepperpy.create()

            # Print request
            console.print(
                Panel(
                    f"[bold blue]Q:[/] {message}",
                    title="Test Request",
                    expand=False,
                )
            )

            # Stream response
            console.print("[bold green]A:[/] ", end="")
            response_text = ""
            async for token in pepper.stream_response(
                message, style=style, format=output_format
            ):
                response_text += token
                if output_format == "markdown":
                    # Clear line and reprint formatted markdown
                    console.print("\r" + " " * len(response_text), end="\r")
                    console.print(Markdown(response_text), end="")
                else:
                    console.print(token, end="")
            console.print()

        except Exception as e:
            console.print(f"\n[red]Test failed: {e}[/]")
            sys.exit(1)

    asyncio.run(run_test())


@cli.command()
def doctor():
    """🏥 Run diagnostics to check Pepperpy setup.

    This command checks:
    - Configuration files
    - API key setup
    - Model availability
    - Connection status
    - Environment setup
    """

    async def run_diagnostics():
        # Check configuration
        config_dir = Path.home() / ".pepperpy"
        config_file = config_dir / "config.env"

        table = Table(
            title="[bold]Pepperpy Diagnostics[/]",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")

        # Check config directory
        if config_dir.exists():
            table.add_row("Config Directory", "✓", str(config_dir))
        else:
            table.add_row("Config Directory", "✗", "Not found")

        # Check config file
        if config_file.exists():
            table.add_row("Config File", "✓", str(config_file))
        else:
            table.add_row("Config File", "✗", "Not found")

        # Check API key
        api_key = None
        if config_file.exists():
            with open(config_file) as f:
                for line in f:
                    if line.startswith("PEPPERPY_API_KEY="):
                        api_key = line.split("=")[1].strip()
                        break

        if api_key:
            table.add_row("API Key", "✓", "Found in config")
        else:
            table.add_row("API Key", "✗", "Not configured")

        # Check environment
        import os

        env_vars = [
            "PEPPERPY_API_KEY",
            "PEPPERPY_MODEL",
            "PEPPERPY_TEMPERATURE",
            "PEPPERPY_MAX_TOKENS",
        ]
        for var in env_vars:
            value = os.getenv(var)
            if value:
                table.add_row(f"Environment: {var}", "✓", "Set")
            else:
                table.add_row(f"Environment: {var}", "-", "Not set")

        # Test connection
        try:
            pepper = await Pepperpy.create()
            response = await pepper.ask("Test message")
            table.add_row("API Connection", "✓", "Successfully connected")
        except Exception as e:
            table.add_row("API Connection", "✗", str(e))

        console.print()
        console.print(table)
        console.print()

        # Print help if issues found
        if not api_key:
            console.print(
                Panel(
                    "[yellow]To configure Pepperpy, run:[/]\n"
                    "  [bold]$ pepperpy init[/]",
                    title="Next Steps",
                    expand=False,
                )
            )

    asyncio.run(run_diagnostics())


@cli.command()
@click.argument("topic", required=False)
@click.option(
    "--depth",
    type=click.Choice(["basic", "detailed", "comprehensive"]),
    default="detailed",
    help="Research depth.",
)
@click.option(
    "--style",
    type=click.Choice(["academic", "business", "casual"]),
    default="business",
    help="Writing style.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["report", "summary", "bullets"]),
    default="report",
    help="Output format.",
)
def research(
    topic: str | None,
    depth: str,
    style: str,
    output_format: str,
):
    """📚 Conduct research on a topic.

    Examples:
        $ pepperpy research "Impact of AI"
        $ pepperpy research "Quantum Computing" --depth comprehensive --style academic
        $ pepperpy research "Climate Change" --format bullets

    """
    if not topic:
        topic = click.prompt("Enter research topic")

    async def run_research():
        try:
            # Create client
            pepper = await Pepperpy.create()

            # Print request
            console.print(
                Panel(
                    f"[bold]Topic:[/] {topic}\n"
                    f"[bold]Depth:[/] {depth}\n"
                    f"[bold]Style:[/] {style}\n"
                    f"[bold]Format:[/] {output_format}",
                    title="Research Request",
                    expand=False,
                )
            )

            # Run research
            console.print("\n[bold]Researching...[/]")
            assert topic is not None  # topic is set by prompt if None
            result = await pepper.research(
                topic,
                depth=depth,
                style=style,
                format=output_format,
            )

            # Print results based on format
            console.print("\n[bold]Results:[/]")
            if output_format == "bullets":
                for point in result.bullets:
                    console.print(f"• {point}")
            elif output_format == "summary":
                console.print(result.tldr)
            else:
                console.print(Markdown(result.full))

            # Print references
            if result.references:
                console.print("\n[bold]References:[/]")
                for ref in result.references:
                    console.print(f"• {ref['title']} ({ref.get('year', 'n/a')})")
                    if "url" in ref:
                        console.print(f"  {ref['url']}")

        except Exception as e:
            console.print(f"\n[red]Research failed: {e}[/]")
            sys.exit(1)

    asyncio.run(run_research())


@cli.command()
@click.argument("message", required=False)
def chat(message: Optional[str]):
    """💬 Start an interactive chat session.

    Examples:
        $ pepperpy chat
        $ pepperpy chat "Tell me about AI"

    During chat:
        - Press Ctrl+C to exit
        - Type /help for commands
        - Type /clear to clear history
        - Type /save to save conversation

    """

    async def run_chat():
        try:
            # Create client
            pepper = await Pepperpy.create()

            # Start chat
            pepper.chat(message)

        except Exception as e:
            console.print(f"\n[red]Chat failed: {e}[/]")
            sys.exit(1)

    asyncio.run(run_chat())


if __name__ == "__main__":
    cli()
