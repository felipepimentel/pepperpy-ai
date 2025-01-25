"""Base extension interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, ClassVar, Union

from pepperpy.core.utils.errors import ExtensionError

T = TypeVar('T', bound='BaseExtension')

class BaseExtension(ABC):
    """Base class for all system extensions.
    
    An extension provides additional functionality to the system through a
    pluggable interface, allowing for modular enhancement of capabilities.
    """
    
    _registry: ClassVar[Dict[str, Type['BaseExtension']]] = {}
    
    @classmethod
    def register(cls, name: str) -> Any:
        """Register an extension class.
        
        Args:
            name: Name to register the extension under.
            
        Returns:
            Decorator function.
        """
        def decorator(extension_cls: Type[T]) -> Type[T]:
            cls._registry[name] = extension_cls
            return extension_cls
        return decorator
    
    @classmethod
    def get_extension(cls, name: str) -> Type['BaseExtension']:
        """Get a registered extension class.
        
        Args:
            name: Name of the extension.
            
        Returns:
            Extension class.
            
        Raises:
            ValueError: If extension is not registered.
        """
        if name not in cls._registry:
            raise ValueError(f"Extension '{name}' not registered")
        return cls._registry[name]
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize extension.
        
        Args:
            name: Extension name
            config: Optional configuration
        """
        if not name:
            raise ValueError("Extension name cannot be empty")
            
        self._name = name
        self._config = config or {}
        self._initialized = False
        
    @property
    def name(self) -> str:
        """Get extension name."""
        return self._name
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get extension configuration."""
        return self._config.copy()
        
    @property
    def is_initialized(self) -> bool:
        """Get initialization status."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize extension."""
        if self.is_initialized:
            return
            
        await self._initialize_impl()
        self._initialized = True
        
    async def cleanup(self) -> None:
        """Clean up extension."""
        if not self.is_initialized:
            return
            
        await self._cleanup_impl()
        self._initialized = False
        
    def validate(self) -> None:
        """Validate extension state."""
        if not self.name:
            raise ValueError("Empty extension name")
            
        self._validate_impl()
        
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
        
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
        
    def _validate_impl(self) -> None:
        """Validate implementation."""
        pass

    @abstractmethod
    async def execute(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an extension command.
        
        Args:
            command: Command to execute
            params: Optional command parameters
            
        Returns:
            Command execution results
            
        Raises:
            ExtensionError: If command execution fails
        """
        pass

    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Get extension metadata.
        
        Returns:
            Dictionary containing extension metadata
        """
        pass

    @abstractmethod
    async def get_dependencies(self) -> List[str]:
        """Get extension dependencies.
        
        Returns:
            List of extension names that this extension depends on
        """
        pass

    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get extension capabilities.
        
        Returns:
            List of capabilities provided by this extension
        """
        pass

    @abstractmethod
    async def get_commands(self) -> Dict[str, Any]:
        """Get supported commands.
        
        Returns:
            Dictionary describing supported commands and their parameters
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get extension status.
        
        Returns:
            Dictionary containing extension status information
        """
        pass 