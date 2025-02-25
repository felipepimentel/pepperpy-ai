"""Agent management commands.

This module provides the implementation for agent-related CLI commands.
It includes commands for creating, listing, and managing agents.
"""

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
) -> list[dict[str, str]]:
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


def display_agents(agents: list[dict[str, str]]) -> None:
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
