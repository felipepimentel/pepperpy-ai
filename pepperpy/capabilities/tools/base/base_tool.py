"""Base tool interface for Pepperpy framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar, ClassVar

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.utils.lifecycle import Lifecycle


class ToolError(PepperpyError):
    """Tool error class."""
    pass


@dataclass
class ToolConfig:
    """Tool configuration."""
    
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T', bound='BaseTool')


class BaseTool(Lifecycle, ABC):
    """Base class for all tools.
    
    A tool is a reusable capability that can be used by agents to perform
    specific tasks or operations.
    """
    
    _registry: ClassVar[Dict[str, Type['BaseTool']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register a tool class.
        
        Args:
            name: Name to register the tool under.
            
        Returns:
            Decorator function.
        """
        def decorator(tool_cls: Type[T]) -> Type[T]:
            cls._registry[name] = tool_cls
            return tool_cls
        return decorator
    
    @classmethod
    def get_tool(cls, name: str) -> Type['BaseTool']:
        """Get a registered tool class.
        
        Args:
            name: Name of the tool.
            
        Returns:
            Tool class.
            
        Raises:
            ValueError: If tool is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Tool '{name}' not registered")
        return cls._registry[name]
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize tool.
        
        Args:
            name: Tool name
            config: Optional configuration
        """
        super().__init__(name, config)
        
        self._config = ToolConfig(
            name=name,
            description=config.get('description', '') if config else '',
            parameters=config.get('parameters', {}) if config else {},
            metadata=config.get('metadata', {}) if config else {},
        )
        
    @property
    def config(self) -> ToolConfig:
        """Get tool configuration."""
        return self._config
        
    async def _initialize_impl(self) -> None:
        """Initialize tool implementation.
        
        Raises:
            ToolError: If initialization fails.
        """
        try:
            await self._setup()
        except Exception as e:
            raise ToolError(f"Failed to initialize tool {self.name}: {e}")
    
    async def _cleanup_impl(self) -> None:
        """Clean up tool implementation.
        
        Raises:
            ToolError: If cleanup fails.
        """
        try:
            await self._teardown()
        except Exception as e:
            raise ToolError(f"Failed to clean up tool {self.name}: {e}")
    
    def _validate_impl(self) -> None:
        """Validate tool implementation.
        
        Raises:
            ToolError: If validation fails.
        """
        try:
            self._validate()
        except Exception as e:
            raise ToolError(f"Failed to validate tool {self.name}: {e}")
    
    @abstractmethod
    async def _setup(self) -> None:
        """Set up tool resources.
        
        This method should be implemented by subclasses to perform
        any necessary setup when the tool is initialized.
        
        Raises:
            Exception: If setup fails.
        """
        pass
        
    @abstractmethod
    async def _teardown(self) -> None:
        """Clean up tool resources.
        
        This method should be implemented by subclasses to perform
        any necessary cleanup when the tool is no longer needed.
        
        Raises:
            Exception: If cleanup fails.
        """
        pass
        
    @abstractmethod
    def _validate(self) -> None:
        """Validate tool configuration.
        
        This method should be implemented by subclasses to validate
        that the tool is properly configured.
        
        Raises:
            Exception: If validation fails.
        """
        pass
        
    @abstractmethod
    async def execute(
        self,
        input: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute tool operation.
        
        Args:
            input: Input data
            context: Optional execution context
            
        Returns:
            Operation result
            
        Raises:
            ToolError: If execution fails
        """
        pass
        
    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata.
        
        Returns:
            Dictionary containing tool metadata
        """
        pass
        
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get tool capabilities.
        
        Returns:
            List of capabilities provided by this tool
        """
        pass
        
    @abstractmethod
    async def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters.
        
        Returns:
            Dictionary describing tool parameters and their types
        """
        pass 