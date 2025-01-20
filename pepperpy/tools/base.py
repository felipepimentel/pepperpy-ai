"""Base tools implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ToolError(PepperpyError):
    """Tool error."""
    pass


class Tool(Lifecycle, ABC):
    """Tool implementation."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize tool.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Optional tool parameters
            config: Optional tool configuration
        """
        super().__init__(name)
        self._description = description
        self._parameters = parameters or {}
        self._config = config or {}
        
    @property
    def description(self) -> str:
        """Return tool description."""
        return self._description
        
    @property
    def parameters(self) -> Dict[str, Any]:
        """Return tool parameters."""
        return self._parameters
        
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
            Execution result
        """
        pass
        
    def validate(self) -> None:
        """Validate tool state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Tool name cannot be empty")
            
        if not self._description:
            raise ValueError("Tool description cannot be empty") 