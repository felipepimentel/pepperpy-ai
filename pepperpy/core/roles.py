"""Role definitions module."""

from dataclasses import dataclass

from ..types import JsonDict


@dataclass
class Role:
    """Role definition."""

    name: str
    description: str
    instructions: str
    metadata: JsonDict | None = None

    def to_dict(self) -> JsonDict:
        """Convert role to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "instructions": self.instructions,
            "metadata": self.metadata or {},
        }
