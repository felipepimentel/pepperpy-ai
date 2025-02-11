"""CLI commands for managing Pepperpy workflows."""

import json
from pathlib import Path
from typing import Optional

import click

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    raise ImportError(
        "The 'rich' package is required for CLI functionality. "
        "Please install it with: pip install rich"
    )

from pepperpy.core.errors import ConfigurationError
from pepperpy.hub.registry import WorkflowRegistry

console = Console()


@click.group()
def workflow():
    """Manage Pepperpy workflows."""
    pass


@workflow.command()
@click.option("--tag", help="Filter workflows by tag")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list(tag: Optional[str], format: str):
    """List available workflows."""
    registry = WorkflowRegistry()
    workflows = registry.list_workflows(tag)

    if format == "json":
        click.echo(json.dumps(workflows, indent=2))
        return

    table = Table(title="Available Workflows")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("Tags")

    for workflow in workflows:
        table.add_row(
            workflow["name"],
            workflow["version"],
            workflow["description"],
            ", ".join(workflow["tags"]),
        )

    console.print(table)


@workflow.command()
@click.argument("workflow_name")
def info(workflow_name: str):
    """Show detailed information about a workflow."""
    registry = WorkflowRegistry()
    try:
        info = registry.get_workflow_info(workflow_name)
        console.print_json(data=info)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {str(e)}")


@workflow.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def validate(path: Path):
    """Validate a workflow configuration file."""
    registry = WorkflowRegistry()
    issues = registry.validate_workflow(path)

    if not issues:
        console.print("[green]Workflow configuration is valid![/green]")
        return

    console.print("[red]Validation issues found:[/red]")
    for issue in issues:
        console.print(f"- {issue}")


@workflow.command()
@click.argument("name")
@click.option(
    "--template",
    default="basic",
    help="Template to use (default: basic)",
)
def create(name: str, template: str):
    """Create a new workflow from a template."""
    registry = WorkflowRegistry()
    try:
        path = registry.create_workflow(name, template)
        console.print(f"[green]Created workflow[/green] {name} at {path}")
    except (ValueError, ConfigurationError) as e:
        console.print(f"[red]Error:[/red] {str(e)}")


if __name__ == "__main__":
    workflow()
