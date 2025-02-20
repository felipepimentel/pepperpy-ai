"""Command groups for the Pepperpy CLI.

This module exposes the following command groups:
- agent: Agent management commands
- config: Configuration management commands
- hub: Hub management commands
- registry: Registry management commands
- run: Execution commands
- tool: Tool management commands
- workflow: Workflow management commands
"""

from pepperpy.cli.commands.agent import agent
from pepperpy.cli.commands.config import config
from pepperpy.cli.commands.hub import hub
from pepperpy.cli.commands.registry import registry
from pepperpy.cli.commands.run import run
from pepperpy.cli.commands.tool import tool
from pepperpy.cli.commands.workflow import workflow

__all__ = [
    "agent",
    "config",
    "hub",
    "registry",
    "run",
    "tool",
    "workflow",
]
