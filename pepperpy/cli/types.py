"""CLI types module.

This module defines types used by the CLI system.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from pepperpy.cli.base import Command, CommandGroup


class CommandType(Enum):
    """Type of command."""

    COMMAND = auto()
    GROUP = auto()


@dataclass
class CommandInfo:
    """Information about a command.

    Attributes:
        name: Command name
        type: Command type
        description: Command description
        parent: Optional parent group name
        aliases: Optional command aliases

    """

    name: str
    type: CommandType
    description: str
    parent: Optional[str] = None
    aliases: Optional[List[str]] = None


# Type aliases
CommandPath = str  # Full command path (e.g. "group subgroup command")
CommandLike = Union[Command, CommandGroup]  # Command or group
CommandArgs = List[str]  # Command arguments
CommandOptions = Dict[str, Any]  # Command options
