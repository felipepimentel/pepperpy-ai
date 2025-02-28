"""Run commands for the Pepperpy CLI.

This module provides commands for:
- Running agents
- Executing workflows
- Invoking tools
- Managing tasks and experiments
- Managing execution state
"""

import asyncio
import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

import click
import yaml
from rich.console import Console
from rich.table import Table

from pepperpy.agents.manager import AgentManager
from pepperpy.agents.providers.services import ProviderRegistry
from pepperpy.cli.exceptions import ExecutionError
from pepperpy.cli.utils import format_error, format_success, load_config
from pepperpy.core.common.messages import ProviderMessage
from pepperpy.core.errors import PepperpyError
from pepperpy.workflows.execution.runtime import WorkflowEngine

# Configure rich console
console = Console()

# Global registries
provider_registry = ProviderRegistry()


@click.group()
def run() -> None:
    """Execute Pepperpy components."""
    pass


@run.command()
@click.argument("agent_id")
@click.option("--task", help="Task to execute")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.option("--timeout", type=int, help="Execution timeout in seconds")
@click.option("--background", is_flag=True, help="Run in background")
def agent(
    agent_id: str, task: str, config: str, timeout: int, background: bool
) -> None:
    """Run an agent.

    AGENT_ID is the ID of the agent to run.
    """
    try:
        # Load config if provided
        config_data = load_config(config) if config else {}

        # Create agent manager
        manager = AgentManager()

        # Prepare execution parameters
        params = {"task": task, "timeout": timeout, **config_data}

        # Execute agent
        if background:
            asyncio.create_task(
                manager.execute_agent(agent_id, [], "default", **params)
            )
            format_success(f"Started agent {agent_id} in background")
        else:
            result = asyncio.run(
                manager.execute_agent(agent_id, [], "default", **params)
            )
            format_success(f"Agent {agent_id} completed successfully")
            console.print(result)

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@run.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--input", type=click.Path(exists=True), help="Input data file")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.option("--timeout", type=int, help="Execution timeout in seconds")
@click.option("--background", is_flag=True, help="Run in background")
def workflow(
    workflow_file: str, input: str, config: str, timeout: int, background: bool
) -> None:
    """Run a workflow.

    WORKFLOW_FILE is the path to the workflow definition file.
    """
    try:
        # Load workflow file
        workflow_path = Path(workflow_file)
        workflow_id = workflow_path.stem

        # Load input data if provided
        input_data = {}
        if input:
            with open(input, "r") as f:
                input_data = json.load(f)

        # Load config if provided
        config_data = load_config(config) if config else {}

        # Create workflow engine
        engine = WorkflowEngine()
        asyncio.run(engine.initialize())

        # Execute workflow
        if background:
            run_id = asyncio.run(
                engine.start_workflow(
                    workflow_id, {**input_data, **config_data, "timeout": timeout}
                )
            )
            format_success(f"Started workflow {workflow_id} (Run ID: {run_id})")
        else:
            result = asyncio.run(
                engine.run_workflow(
                    workflow_id, {**input_data, **config_data, "timeout": timeout}
                )
            )
            format_success(f"Workflow {workflow_id} completed successfully")
            console.print(result)

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@run.command()
@click.argument("tool_name")
@click.option("--input", type=click.Path(exists=True), help="Input data file")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.option("--timeout", type=int, help="Execution timeout in seconds")
def tool(tool_name: str, input: str, config: str, timeout: int) -> None:
    """Run a tool.

    TOOL_NAME is the name of the tool to run.
    """
    try:
        # Load input data if provided
        input_data = {}
        if input:
            with open(input, "r") as f:
                input_data = json.load(f)

        # Load config if provided
        config_data = load_config(config) if config else {}

        # Initialize provider registry
        asyncio.run(provider_registry.initialize())

        # Get tool provider
        provider_class = provider_registry.providers.get(tool_name)
        if not provider_class:
            raise ExecutionError(
                component_type="tool",
                component_id=tool_name,
                reason=f"Tool provider '{tool_name}' not registered",
            )

        # Create tool instance
        tool_instance = provider_class(uuid4())

        # Execute tool
        try:
            # Create provider message
            message = ProviderMessage(
                content=json.dumps(input_data),
                provider_type=tool_name,
                metadata={"timeout": timeout, **config_data},
            )

            # Execute tool with message
            result = asyncio.run(tool_instance.execute(message=message))
            format_success(f"Tool {tool_name} completed successfully")
            console.print(result)

        finally:
            # Cleanup
            asyncio.run(provider_registry.cleanup())

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@run.command()
@click.argument("task_file", type=click.Path(exists=True))
@click.option("--async", "is_async", is_flag=True, help="Run asynchronously")
@click.option("--output", type=click.Path(), help="Output file for results")
def task(task_file: str, is_async: bool, output: Optional[str]) -> None:
    """Run a task from a definition file.

    TASK_FILE: Path to task definition file (YAML/JSON)
    """
    try:
        # Load task definition
        task_path = Path(task_file)
        with open(task_path) as f:
            if task_path.suffix == ".json":
                definition = json.load(f)
            else:
                definition = yaml.safe_load(f)

        # TODO: Implement task execution
        result = {"status": "completed", "output": "Task result"}

        if output:
            Path(output).write_text(json.dumps(result, indent=2))
            format_success(f"Results written to {output}")
        else:
            console.print("\n[bold]Task Results[/bold]")
            console.print(json.dumps(result, indent=2))

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@run.command()
@click.argument("experiment_file", type=click.Path(exists=True))
@click.option("--name", help="Experiment name")
@click.option("--tags", help="Comma-separated tags")
def experiment(experiment_file: str, name: Optional[str], tags: Optional[str]) -> None:
    """Run an experiment from a definition file.

    EXPERIMENT_FILE: Path to experiment definition file (YAML/JSON)
    """
    try:
        # Load experiment definition
        exp_path = Path(experiment_file)
        with open(exp_path) as f:
            if exp_path.suffix == ".json":
                definition = json.load(f)
            else:
                definition = yaml.safe_load(f)

        # Set name and tags
        if name:
            definition["name"] = name
        if tags:
            definition["tags"] = tags.split(",")

        # TODO: Implement experiment execution
        format_success(f"Started experiment: {definition['name']}")

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@run.command()
@click.argument("run_id")
def logs(run_id: str) -> None:
    """Get logs for a run.

    RUN_ID: ID of the run
    """
    try:
        # TODO: Implement log retrieval
        console.print("\n[bold]Run Logs[/bold]")
        console.print("[12:00:00] Started run")
        console.print("[12:00:01] Processing...")
        console.print("[12:00:02] Completed")

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@run.command()
@click.argument("run_id")
def stop(run_id: str) -> None:
    """Stop a running task or experiment.

    RUN_ID: ID of the run to stop
    """
    try:
        if not click.confirm(f"Stop run {run_id}?"):
            return

        # TODO: Implement run stopping
        format_success(f"Stopped run: {run_id}")

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()


@run.command()
@click.option("--type", help="Filter by run type")
@click.option("--status", help="Filter by status")
@click.option("--tag", help="Filter by tag")
def list(type: Optional[str], status: Optional[str], tag: Optional[str]) -> None:
    """List runs."""
    try:
        # TODO: Implement run listing
        table = Table(title="Runs")
        table.add_column("ID")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Started")
        table.add_column("Tags")

        # Add dummy data for now
        table.add_row(
            "run-123",
            "task",
            "completed",
            "2024-01-01 12:00:00",
            "tag1, tag2",
        )
        table.add_row(
            "run-456",
            "experiment",
            "running",
            "2024-01-01 12:30:00",
            "tag3",
        )

        console.print(table)

    except PepperpyError as e:
        format_error(str(e))
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")
        raise click.Abort()
