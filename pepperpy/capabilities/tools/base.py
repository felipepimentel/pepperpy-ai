"""Base tool implementation.

This module provides the base classes for implementing tools in the Pepperpy framework,
aligned with the provider system architecture.
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, ClassVar, Type

from ..interfaces import Tool
from ..providers.base import BaseProvider, ProviderRegistry

@dataclass
class ToolConfig:
    """Tool configuration."""
    
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseTool(BaseProvider, Tool):
    """Base class for all tools."""
    
    registry: ClassVar[ProviderRegistry] = ProviderRegistry()
    
    def __init__(
        self,
        tool_cfg: ToolConfig,
        dependencies: Optional[Dict[str, BaseProvider]] = None,
    ) -> None:
        """Initialize tool.
        
        Args:
            tool_cfg: Tool configuration
            dependencies: Optional tool dependencies
        """
        if not tool_cfg.name:
            raise ValueError("Tool name cannot be empty")
            
        # Store tool configuration
        self._tool_config = tool_cfg
        self._dependencies = dependencies or {}
        
        # Create provider configuration
        provider_cfg = {"parameters": tool_cfg.parameters}
        provider_cfg.update(tool_cfg.metadata)
        
        # Initialize base provider attributes
        self._name = tool_cfg.name
        self._config = provider_cfg
        self._initialized = False
        self._initialized_at = None
        self._cleaned_up = False
        self._cleaned_up_at = None
    
    @property
    def name(self) -> str:
        """Get tool name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get tool description."""
        return self._tool_config.description
    
    @property
    def is_initialized(self) -> bool:
        """Get initialization status."""
        return self._initialized
    
    @property
    def dependencies(self) -> Dict[str, BaseProvider]:
        """Get tool dependencies."""
        return self._dependencies.copy()
    
    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute tool.
        
        This method handles initialization checking and provides
        a consistent execution flow. The actual tool logic should
        be implemented in _execute_impl.
        
        Args:
            input_data: Input data
            context: Optional execution context
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If tool is not initialized
        """
        if not self.is_initialized:
            raise ValueError("Tool not initialized")
            
        return await self._execute_impl(input_data, context)
    
    async def _initialize_impl(self) -> None:
        """Initialize tool and its dependencies."""
        # Initialize dependencies first
        for dep in self._dependencies.values():
            if not dep.is_initialized:
                await dep.initialize()
        
        # Then initialize tool-specific resources
        await self._setup()
    
    async def _cleanup_impl(self) -> None:
        """Clean up tool and its dependencies."""
        try:
            # Clean up tool-specific resources first
            await self._teardown()
        finally:
            # Then clean up dependencies
            for dep in reversed(list(self._dependencies.values())):
                if dep.is_initialized:
                    await dep.cleanup()
    
    def _validate_impl(self) -> None:
        """Validate tool state."""
        if not self._name:
            raise ValueError("Empty tool name")
            
        if not self._tool_config.description:
            raise ValueError("Empty tool description")
            
        # Validate dependencies
        for name, dep in self._dependencies.items():
            if not name:
                raise ValueError("Empty dependency name")
            if not dep:
                raise ValueError(f"Missing dependency: {name}")
            dep.validate()
    
    @abstractmethod
    async def _setup(self) -> None:
        """Set up tool-specific resources."""
        pass
    
    @abstractmethod
    async def _teardown(self) -> None:
        """Clean up tool-specific resources."""
        pass
    
    @abstractmethod
    async def _execute_impl(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Implementation-specific tool execution.
        
        This method should be overridden by tool implementations
        to provide the actual tool logic.
        
        Args:
            input_data: Input data
            context: Optional execution context
            
        Returns:
            Tool result
        """
        raise NotImplementedError 