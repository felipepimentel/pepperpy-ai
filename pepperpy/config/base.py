"""Base configuration module."""

from dataclasses import dataclass, field
from typing import Any, cast

from ..types import JsonDict


@dataclass
class BaseConfig:
    """Base configuration class."""

    name: str
    version: str
    enabled: bool = True
    metadata: JsonDict = field(default_factory=dict)
    settings: dict[str, Any] | None = None

    def to_dict(self) -> JsonDict:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "BaseConfig":
        """Create configuration from dictionary."""
        name = cast(str, data["name"])
        version = cast(str, data["version"])
        enabled = cast(bool, data.get("enabled", True))
        metadata = cast(JsonDict, data.get("metadata", {}))
        settings = cast(dict[str, Any] | None, data.get("settings"))

        return cls(
            name=name,
            version=version,
            enabled=enabled,
            metadata=metadata,
            settings=settings,
        )


__all__ = ["BaseConfig"]
