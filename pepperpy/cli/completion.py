"""Shell completion for the Pepperpy CLI.

This module provides shell completion functionality for:
- Command names and options
- File paths
- Provider and capability names
- Agent and workflow IDs
"""

import os
from pathlib import Path
from typing import List

from click.shell_completion import CompletionItem


def get_commands() -> List[str]:
    """Get a list of available commands.

    Returns:
        List of command names.
    """
    return [
        "agent",
        "config",
        "hub",
        "registry",
        "run",
        "tool",
        "workflow",
    ]


def get_providers() -> List[str]:
    """Get a list of registered providers.

    Returns:
        List of provider names.
    """
    # TODO: Implement provider listing
    return []


def get_capabilities() -> List[str]:
    """Get a list of registered capabilities.

    Returns:
        List of capability names.
    """
    # TODO: Implement capability listing
    return []


def get_agents() -> List[str]:
    """Get a list of available agents.

    Returns:
        List of agent IDs.
    """
    # TODO: Implement agent listing
    return []


def get_workflows() -> List[str]:
    """Get a list of available workflows.

    Returns:
        List of workflow IDs.
    """
    # TODO: Implement workflow listing
    return []


def get_tools() -> List[str]:
    """Get a list of available tools.

    Returns:
        List of tool names.
    """
    # TODO: Implement tool listing
    return []


def complete_command(incomplete: str) -> List[CompletionItem]:
    """Complete command names.

    Args:
        incomplete: The incomplete command name.

    Returns:
        List of matching completion items.
    """
    return [CompletionItem(cmd) for cmd in get_commands() if cmd.startswith(incomplete)]


def complete_provider(incomplete: str) -> List[CompletionItem]:
    """Complete provider names.

    Args:
        incomplete: The incomplete provider name.

    Returns:
        List of matching completion items.
    """
    return [
        CompletionItem(provider)
        for provider in get_providers()
        if provider.startswith(incomplete)
    ]


def complete_capability(incomplete: str) -> List[CompletionItem]:
    """Complete capability names.

    Args:
        incomplete: The incomplete capability name.

    Returns:
        List of matching completion items.
    """
    return [
        CompletionItem(capability)
        for capability in get_capabilities()
        if capability.startswith(incomplete)
    ]


def complete_agent(incomplete: str) -> List[CompletionItem]:
    """Complete agent IDs.

    Args:
        incomplete: The incomplete agent ID.

    Returns:
        List of matching completion items.
    """
    return [
        CompletionItem(agent) for agent in get_agents() if agent.startswith(incomplete)
    ]


def complete_workflow(incomplete: str) -> List[CompletionItem]:
    """Complete workflow IDs.

    Args:
        incomplete: The incomplete workflow ID.

    Returns:
        List of matching completion items.
    """
    return [
        CompletionItem(workflow)
        for workflow in get_workflows()
        if workflow.startswith(incomplete)
    ]


def complete_tool(incomplete: str) -> List[CompletionItem]:
    """Complete tool names.

    Args:
        incomplete: The incomplete tool name.

    Returns:
        List of matching completion items.
    """
    return [CompletionItem(tool) for tool in get_tools() if tool.startswith(incomplete)]


def complete_path(incomplete: str) -> List[CompletionItem]:
    """Complete file paths.

    Args:
        incomplete: The incomplete path.

    Returns:
        List of matching completion items.
    """
    if not incomplete:
        incomplete = "."

    path = Path(incomplete)
    if not path.is_absolute():
        path = Path.cwd() / path

    try:
        parent = path.parent
        if not parent.exists():
            return []

        name = path.name
        paths = []
        for entry in parent.iterdir():
            if entry.name.startswith(name):
                if entry.is_dir():
                    paths.append(CompletionItem(str(entry) + os.sep))
                else:
                    paths.append(CompletionItem(str(entry)))
        return paths
    except Exception:
        return []
