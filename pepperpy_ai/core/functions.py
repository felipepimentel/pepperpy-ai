"""Function definitions module."""

from dataclasses import dataclass

from ..types import JsonDict


@dataclass
class Function:
    """Function definition."""

    name: str
    description: str
    parameters: JsonDict
    metadata: JsonDict | None = None

    def to_dict(self) -> JsonDict:
        """Convert function to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "metadata": self.metadata or {},
        }


@dataclass
class FunctionCall:
    """Function call."""

    name: str
    arguments: str
    metadata: JsonDict | None = None

    def to_dict(self) -> JsonDict:
        """Convert function call to dictionary."""
        return {
            "name": self.name,
            "arguments": self.arguments,
            "metadata": self.metadata or {},
        }
