"""Workflow commands for the Pepperpy CLI.

This module provides commands for:
- Creating workflows
- Running workflows
- Managing workflow configuration
- Listing available workflows
"""

import click
from rich.console import Console

from pepperpy.core.errors import PepperpyError

# Configure rich console
console = Console()


@click.group()
def workflow() -> None:
    """Manage Pepperpy workflows."""
    pass


@workflow.command()
@click.argument("name")
@click.option("--template", help="Workflow template to use")
@click.option("--config", type=click.Path(exists=True), help="Config file")
def create(name: str, template: str, config: str) -> None:
    """Create a new workflow.

    NAME is the name of the workflow to create.
    """
    try:
        # TODO: Implement workflow creation
        console.print(f"[green]Created workflow:[/green] {name}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@workflow.command()
@click.argument("name")
@click.option("--input", help="Input data")
@click.option("--config", type=click.Path(exists=True), help="Config file")
def run(name: str, input: str, config: str) -> None:
    """Run a workflow.

    NAME is the name of the workflow to run.
    """
    try:
        # TODO: Implement workflow execution
        console.print(f"[green]Running workflow:[/green] {name}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@workflow.command()
@click.argument("name")
@click.option("--key", help="Config key to get/set")
@click.option("--value", help="Value to set")
def config(name: str, key: str, value: str) -> None:
    """Manage workflow configuration.

    NAME is the name of the workflow to configure.
    """
    try:
        # TODO: Implement config management
        if value:
            console.print(f"[green]Set config:[/green] {key}={value}")
        else:
            console.print(f"[green]Config value:[/green] {key}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@workflow.command()
def list() -> None:
    """List available workflows."""
    try:
        # TODO: Implement workflow listing
        console.print("[green]Available workflows:[/green]")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


"""Workflow commands for the Pepperpy CLI.

This module provides commands for managing workflows:
- Creating and deploying workflows
- Running and monitoring workflows
- Managing workflow state and history
- Validating workflow definitions
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from pepperpy.monitoring import audit_logger
from pepperpy.workflows import WorkflowEngine, WorkflowState

console = Console()


@click.group()
def workflow() -> None:
    """Manage Pepperpy workflows."""


@workflow.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--name", help="Workflow name (defaults to filename)")
@click.option("--description", help="Workflow description")
def deploy(
    workflow_file: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """Deploy a workflow from a definition file.

    WORKFLOW_FILE: Path to workflow definition file (YAML/JSON)
    """
    try:
        # Load workflow definition
        workflow_path = Path(workflow_file)
        with open(workflow_path) as f:
            if workflow_path.suffix == ".json":
                definition = json.load(f)
            else:
                import yaml  # type: ignore

                definition = yaml.safe_load(f)

        # Set name and description
        if name:
            definition["name"] = name
        if description:
            definition["description"] = description

        # Initialize workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Deploy workflow
        workflow_id = asyncio.run(engine.deploy_workflow(definition))

        # Log deployment
        asyncio.run(
            audit_logger.log({
                "event_type": "workflow.deploy",
                "workflow_id": workflow_id,
                "name": definition["name"],
                "source_file": str(workflow_path),
            })
        )

        console.print(f"Successfully deployed workflow: {workflow_id}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@workflow.command()
@click.argument("workflow_id")
@click.option(
    "--input", "input_file", type=click.Path(exists=True), help="Input file (JSON)"
)
@click.option("--async", "is_async", is_flag=True, help="Run asynchronously")
def run(
    workflow_id: str, input_file: Optional[str] = None, is_async: bool = False
) -> None:
    """Run a workflow.

    WORKFLOW_ID: ID of the workflow to run
    """
    try:
        # Load input data
        input_data = {}
        if input_file:
            with open(input_file) as f:
                input_data = json.load(f)

        # Initialize workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Run workflow
        if is_async:
            run_id = asyncio.run(engine.start_workflow(workflow_id, input_data))
            console.print(f"Started workflow run: {run_id}")
        else:
            result = asyncio.run(engine.run_workflow(workflow_id, input_data))
            console.print("\n[bold]Workflow Result[/bold]")
            console.print(json.dumps(result, indent=2))

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@workflow.command()
@click.argument("run_id")
def status(run_id: str) -> None:
    """Get status of a workflow run.

    RUN_ID: ID of the workflow run
    """
    try:
        # Initialize workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Get run status
        status = asyncio.run(engine.get_run_status(run_id))

        # Display status
        console.print("\n[bold]Workflow Run Status[/bold]")
        console.print(f"State: {status.state.name}")
        console.print(f"Started: {status.started_at}")
        if status.completed_at:
            console.print(f"Completed: {status.completed_at}")
        if status.error:
            console.print(f"Error: {status.error}")

        # Display step status
        console.print("\n[bold]Step Status[/bold]")
        table = Table()
        table.add_column("Step ID")
        table.add_column("State")
        table.add_column("Started")
        table.add_column("Completed")
        table.add_column("Error")

        for step_id, step_status in status.steps.items():
            table.add_row(
                step_id,
                step_status.state.name,
                str(step_status.started_at) if step_status.started_at else "",
                str(step_status.completed_at) if step_status.completed_at else "",
                str(step_status.error) if step_status.error else "",
            )

        console.print(table)

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@workflow.command()
@click.argument("run_id")
def logs(run_id: str) -> None:
    """Get logs for a workflow run.

    RUN_ID: ID of the workflow run
    """
    try:
        # Initialize workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Get run logs
        logs = asyncio.run(engine.get_run_logs(run_id))

        # Display logs
        console.print("\n[bold]Workflow Run Logs[/bold]")
        for log in logs:
            console.print(
                f"[{log.timestamp}] [{log.level}] {log.message}",
                style="red" if log.level == "ERROR" else None,
            )

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@workflow.command()
@click.argument("run_id")
def stop(run_id: str) -> None:
    """Stop a running workflow.

    RUN_ID: ID of the workflow run to stop
    """
    try:
        # Initialize workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Stop workflow run
        asyncio.run(engine.stop_workflow(run_id))

        # Log stop event
        asyncio.run(
            audit_logger.log({
                "event_type": "workflow.stop",
                "run_id": run_id,
            })
        )

        console.print(f"Successfully stopped workflow run: {run_id}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@workflow.command()
@click.argument("workflow_id")
def delete(workflow_id: str) -> None:
    """Delete a workflow.

    WORKFLOW_ID: ID of the workflow to delete
    """
    try:
        if not click.confirm(f"Delete workflow {workflow_id}?"):
            return

        # Initialize workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Delete workflow
        asyncio.run(engine.delete_workflow(workflow_id))

        # Log deletion
        asyncio.run(
            audit_logger.log({
                "event_type": "workflow.delete",
                "workflow_id": workflow_id,
            })
        )

        console.print(f"Successfully deleted workflow: {workflow_id}")

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()


@workflow.command()
@click.option("--state", type=click.Choice([s.name for s in WorkflowState]))
def list(state: Optional[str] = None) -> None:
    """List workflows."""
    try:
        # Initialize workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Get workflows
        workflows = asyncio.run(
            engine.list_workflows(state=WorkflowState[state] if state else None)
        )

        # Display workflows
        table = Table(title="Workflows")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("State")
        table.add_column("Created")
        table.add_column("Last Run")

        for workflow in workflows:
            table.add_row(
                str(workflow["id"]),
                str(workflow["name"]),
                str(workflow["state"].name),
                str(workflow["created_at"]) if workflow["created_at"] else "",
                str(workflow["last_run_at"]) if workflow["last_run_at"] else "",
            )

        console.print(table)

    except PepperpyError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.recovery_hint:
            console.print(f"[yellow]Hint: {e.recovery_hint}[/yellow]")
        raise click.Abort()
