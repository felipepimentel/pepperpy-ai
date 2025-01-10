"""Team configuration."""

from dataclasses import dataclass, field

from .base import BaseConfigData, JsonDict


@dataclass
class TeamConfig(BaseConfigData):
    """Team configuration."""

    # Required fields first (no defaults)
    name: str
    members: list[str]
    roles: dict[str, str]

    # Optional fields (with defaults)
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
