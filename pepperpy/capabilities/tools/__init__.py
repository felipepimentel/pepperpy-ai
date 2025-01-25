"""Tools module for managing tool implementations.

This module provides the base classes and type definitions for implementing
and managing tools in the Pepperpy framework.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseTool, ToolConfig
from ..core.errors import PepperpyError

logger = logging.getLogger(__name__)


class ToolError(PepperpyError):
    """Tool error."""
    pass


@dataclass
class ToolInput:
    """Tool input data."""
    
    data: Any
    context: Optional[Dict[str, Any]] = None


@dataclass
class ToolResult:
    """Tool execution result."""
    
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Re-export core tools
from .functions.core import (
    APITool,
    CircuitBreaker,
    TokenHandler,
)
from .functions.core.function import Function


__all__ = [
    "ToolError",
    "ToolConfig",
    "ToolInput",
    "ToolResult",
    "BaseTool",
    "Function",
    "APITool",
    "CircuitBreaker",
    "TokenHandler",
]
