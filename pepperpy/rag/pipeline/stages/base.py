"""Base classes for RAG pipeline stages.

This module provides the base classes for all RAG pipeline stages,
including the StageConfig base class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class StageConfig:
    """Base configuration for pipeline stages."""

    name: str
    type: str
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)
