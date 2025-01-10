"""Module configuration."""

from dataclasses import dataclass, field
from typing import Any

from .base import BaseConfig


@dataclass
class ModuleConfig(BaseConfig):
    """Base module configuration."""

    name: str
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
