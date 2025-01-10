"""Base configuration types."""

from dataclasses import dataclass, field
from typing import Any

JsonDict = dict[str, Any]


@dataclass
class BaseConfigData:
    """Base configuration data without defaults."""

    name: str


@dataclass
class BaseConfig(BaseConfigData):
    """Base configuration with defaults."""

    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
