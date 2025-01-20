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

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.tools.functions.api import APIFunction, CircuitBreaker
from pepperpy.tools.functions.auth import TokenHandler
from pepperpy.tools.functions.files import FileHandler
from pepperpy.tools.functions.code import CodeHandler
from pepperpy.tools.functions.search import SearchHandler
from pepperpy.tools.functions.shell import ShellHandler
from pepperpy.tools.functions.docs import DocumentLoader
from pepperpy.tools.functions.ai import LLMManager, BaseLLM, StabilityAI
from pepperpy.tools.functions.vision import VisionHandler
from pepperpy.tools.functions.web import SerpHandler
from pepperpy.tools.functions.media import ElevenLabs
from pepperpy.tools.functions.system import TerminalHandler


logger = logging.getLogger(__name__)


class ToolError(PepperpyError):
    """Tool error."""
    pass


@dataclass
class ToolConfig:
    """Tool configuration."""
    
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


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


class Tool(Lifecycle, ABC):
    """Base class for tools."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize tool.
        
        Args:
            name: Tool name
            config: Optional tool configuration
        """
        super().__init__(name)
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return tool configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize tool."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up tool."""
        pass
        
    @abstractmethod
    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute tool.
        
        Args:
            input_data: Input data
            context: Optional execution context
            
        Returns:
            Tool result
        """
        pass
        
    def validate(self) -> None:
        """Validate tool state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Tool name cannot be empty")


__all__ = [
    "ToolError",
    "ToolConfig",
    "ToolInput",
    "ToolResult",
    "Tool",
    "APIFunction",
    "CircuitBreaker",
    "TokenHandler",
    "FileHandler",
    "CodeHandler",
    "SearchHandler",
    "ShellHandler",
    "DocumentLoader",
    "LLMManager",
    "BaseLLM",
    "StabilityAI",
    "VisionHandler",
    "SerpHandler",
    "ElevenLabs",
    "TerminalHandler",
]
