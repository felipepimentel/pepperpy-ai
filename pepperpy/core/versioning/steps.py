"""Migration steps for version management."""

from dataclasses import dataclass, field
from typing import Any, Dict

from .types import Version


@dataclass
class MigrationContext:
    """Context for migration operations."""

    component: str
    from_version: Version
    to_version: Version
    data: Dict[str, Any] = field(default_factory=dict)
    backup: Dict[str, Any] = field(default_factory=dict)
