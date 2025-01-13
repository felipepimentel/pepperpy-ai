"""Base configuration module."""

from dataclasses import dataclass, field
from typing import Any

from pepperpy_core.types import JsonDict


@dataclass
class BaseConfig:
    """Base configuration class."""

    name: str
    version: str
    metadata: JsonDict = field(default_factory=dict)
    settings: dict[str, Any] | None = None

    def to_dict(self) -> JsonDict:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "metadata": self.metadata,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "BaseConfig":
        """Create configuration from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            metadata=data.get("metadata", {}),
            settings=data.get("settings"),
        )


__all__ = ["BaseConfig"]
