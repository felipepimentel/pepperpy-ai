"""Agent management commands.

This module provides the implementation for agent-related CLI commands.
It includes commands for creating, listing, and managing agents.
"""

import builtins

import click
from rich.console import Console
from rich.table import Table

from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.agents.registry import AgentRegistry
from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Configure console
console = Console()


@click.group()
def agent() -> None:
    """Agent management commands."""
    pass


@agent.command()
@click.argument("name")
@click.argument("agent_type")
@click.option("--description", help="Agent description")
@click.option("--param", "-p", multiple=True, help="Agent parameters (key=value)")
async def create(
    name: str,
    agent_type: str,
    description: str | None = None,
    param: list[str] | None = None,
) -> None:
    """Create a new agent."""
    try:
        # Parse parameters
        parameters = {}
        if param:
            for p in param:
                key, value = p.split("=", 1)
                parameters[key.strip()] = value.strip()

        # Create agent
        agent_id = await create_agent(
            name=name,
            agent_type=agent_type,
            description=description,
            parameters=parameters,
        )

        console.print(f"[green]Created agent:[/green] {agent_id}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {e}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")


@agent.command()
@click.option("--type", "agent_type", help="Filter by agent type")
@click.option("--status", help="Filter by agent status")
async def list(agent_type: str | None = None, status: str | None = None) -> None:
    """List available agents."""
    try:
        agents = await list_agents(agent_type=agent_type, status=status)
        display_agents(agents)

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {e}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")


@agent.command()
@click.argument("agent_id")
async def delete(agent_id: str) -> None:
    """Delete an agent."""
    try:
        await delete_agent(agent_id)
        console.print(f"[green]Deleted agent:[/green] {agent_id}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {e}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")


@agent.command()
@click.argument("agent_id")
@click.option("--name", help="New agent name")
@click.option("--description", help="New agent description")
@click.option("--param", "-p", multiple=True, help="New agent parameters (key=value)")
async def update(
    agent_id: str,
    name: str | None = None,
    description: str | None = None,
    param: builtins.list[str] | None = None,
) -> None:
    """Update an agent."""
    try:
        # Parse parameters
        parameters = {}
        if param:
            for p in param:
                key, value = p.split("=", 1)
                parameters[key.strip()] = value.strip()

        # Update agent
        await update_agent(
            agent_id=agent_id,
            name=name,
            description=description,
            parameters=parameters,
        )

        console.print(f"[green]Updated agent:[/green] {agent_id}")

    except PepperpyError as e:
        console.print(f"[red]Error:[/red] {e}")
        if e.recovery_hint:
            console.print(f"[yellow]Hint:[/yellow] {e.recovery_hint}")


# Helper functions
async def create_agent(
    name: str,
    agent_type: str,
    description: str | None = None,
    parameters: dict[str, str] | None = None,
) -> str:
    """Create a new agent.

    Args:
        name: Agent name
        agent_type: Type of agent
        description: Optional agent description
        parameters: Optional agent parameters

    Returns:
        str: Agent ID

    Raises:
        PepperpyError: If agent creation fails
    """
    try:
        # Create agent configuration
        config = AgentConfig(
            name=name,
            description=description or f"{agent_type.title()} agent",
            parameters=parameters or {},
        )

        # Create agent instance
        agent = BaseAgent(
            name=name,
            version="0.1.0",
            config=config,
        )

        # Register agent
        registry = AgentRegistry()
        agent_id = await registry.register(agent)

        return agent_id

    except Exception as e:
        raise PepperpyError(
            message=f"Failed to create agent: {e}",
            details={
                "name": name,
                "type": agent_type,
                "description": description,
            },
            recovery_hint="Check agent configuration and try again",
        )


async def list_agents(
    agent_type: str | None = None,
    status: str | None = None,
) -> builtins.list[dict[str, str]]:
    """List available agents.

    Args:
        agent_type: Optional agent type filter
        status: Optional status filter

    Returns:
        List[Dict[str, str]]: List of agent information

    Raises:
        PepperpyError: If agent listing fails
    """
    try:
        # Get agent registry
        registry = AgentRegistry()

        # List agents with filters
        agents = await registry.list(
            filters={
                "type": agent_type,
                "status": status,
            }
            if agent_type or status
            else None
        )

        # Format agent information
        result = []
        for agent in agents:
            result.append({
                "id": agent.id,
                "name": agent.name,
                "type": agent.type,
                "status": agent.status,
                "description": agent.description,
            })

        return result

    except Exception as e:
        raise PepperpyError(
            message=f"Failed to list agents: {e}",
            details={
                "type": agent_type,
                "status": status,
            },
            recovery_hint="Check agent registry and try again",
        )


def display_agents(agents: builtins.list[dict[str, str]]) -> None:
    """Display agents in a formatted table.

    Args:
        agents: List of agent information
    """
    # Create table
    table = Table(
        title="Available Agents",
        show_header=True,
        header_style="bold magenta",
    )

    # Add columns
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Description")

    # Add rows
    for agent in agents:
        table.add_row(
            agent["id"],
            agent["name"],
            agent["type"],
            agent["status"],
            agent["description"],
        )

    # Display table
    console.print(table)


async def delete_agent(agent_id: str) -> None:
    """Delete an agent.

    Args:
        agent_id: ID of the agent to delete

    Raises:
        PepperpyError: If agent deletion fails
    """
    try:
        # Get agent registry
        registry = AgentRegistry()

        # Delete agent
        await registry.delete(agent_id)

    except Exception as e:
        raise PepperpyError(
            message=f"Failed to delete agent: {e}",
            details={"agent_id": agent_id},
            recovery_hint="Check agent ID and try again",
        )


async def update_agent(
    agent_id: str,
    name: str | None = None,
    description: str | None = None,
    parameters: dict[str, str] | None = None,
) -> None:
    """Update an agent.

    Args:
        agent_id: ID of the agent to update
        name: Optional new name
        description: Optional new description
        parameters: Optional new parameters

    Raises:
        PepperpyError: If agent update fails
    """
    try:
        # Get agent registry
        registry = AgentRegistry()

        # Get current agent
        agent = await registry.get(agent_id)
        if not agent:
            raise PepperpyError(
                message=f"Agent not found: {agent_id}",
                details={"agent_id": agent_id},
                recovery_hint="Check agent ID and try again",
            )

        # Update agent configuration
        config = agent.config
        if name:
            config.name = name
        if description:
            config.description = description
        if parameters:
            config.parameters.update(parameters)

        # Update agent
        await registry.update(agent_id, agent)

    except PepperpyError:
        raise
    except Exception as e:
        raise PepperpyError(
            message=f"Failed to update agent: {e}",
            details={
                "agent_id": agent_id,
                "name": name,
                "description": description,
            },
            recovery_hint="Check agent configuration and try again",
        )
