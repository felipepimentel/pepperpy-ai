"""Core extension system for the Pepperpy framework.

This module provides the extension system that allows extending and customizing
the framework's behavior through extension points. Key features:
- Extension point registration and discovery
- Extension lifecycle management
- Extension configuration and validation
- Extension dependency resolution
"""

import asyncio
from abc import abstractmethod
from datetime import datetime
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    Type,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import ExtensionError
from pepperpy.core.types import ComponentState
from pepperpy.core.events import EventBus
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)

# Type variables for generic implementations
T = TypeVar("T")
T_Config = TypeVar("T_Config", bound=BaseModel)


class ExtensionMetadata(BaseModel):
    """Metadata for extensions.

    Attributes:
        id: Unique extension identifier
        name: Extension name
        version: Extension version
        description: Extension description
        author: Extension author
        created_at: When extension was created
        updated_at: When extension was last updated
        config: Extension configuration
        dependencies: Extension dependencies
        tags: Extension tags
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(description="Extension name")
    version: str = Field(description="Extension version")
    description: str = Field(default="", description="Extension description")
    author: str = Field(default="", description="Extension author")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    config: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    tags: Set[str] = Field(default_factory=set)


class Extension(Generic[T_Config], Lifecycle):
    """Base class for all extensions.

    This class provides the core functionality for extensions:
    - Lifecycle management (initialize, start, stop)
    - Configuration handling
    - Event handling
    - Error handling
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[T_Config] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize extension.

        Args:
            name: Extension name
            version: Extension version
            config: Optional extension configuration
            event_bus: Optional event bus for extension events
        """
        super().__init__()
        self._metadata = ExtensionMetadata(
            name=name,
            version=version,
        )
        self._config = config
        self._event_bus = event_bus
        self._state = ComponentState.UNREGISTERED

    @property
    def metadata(self) -> ExtensionMetadata:
        """Get extension metadata."""
        return self._metadata

    @property
    def config(self) -> Optional[T_Config]:
        """Get extension configuration."""
        return self._config

    async def initialize(self) -> None:
        """Initialize the extension.

        This method is called during extension startup to perform any necessary
        initialization.

        Raises:
            ExtensionError: If initialization fails
        """
        try:
            self._state = ComponentState.INITIALIZED
            # Initialize extension
            await self._initialize()
            self._state = ComponentState.RUNNING
            logger.info(f"Extension {self.metadata.name} initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            raise ExtensionError(f"Failed to initialize extension: {e}") from e

    async def cleanup(self) -> None:
        """Clean up extension resources.

        This method is called during extension shutdown to perform any necessary
        cleanup.
        """
        try:
            await self._cleanup()
            self._state = ComponentState.STOPPED
            logger.info(f"Extension {self.metadata.name} cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to clean up extension: {e}")

    @abstractmethod
    async def _initialize(self) -> None:
        """Initialize extension resources.

        This method should be overridden by extension implementations
        that need initialization.

        Raises:
            ExtensionError: If initialization fails
        """
        pass

    @abstractmethod
    async def _cleanup(self) -> None:
        """Clean up extension resources.

        This method should be overridden by extension implementations
        that need cleanup.
        """
        pass


@runtime_checkable
class ExtensionProtocol(Protocol):
    """Protocol defining required extension interface."""

    @property
    def metadata(self) -> ExtensionMetadata:
        """Get extension metadata."""
        ...

    async def initialize(self) -> None:
        """Initialize extension."""
        ...

    async def cleanup(self) -> None:
        """Clean up extension resources."""
        ...


T_Extension = TypeVar("T_Extension", bound=ExtensionProtocol)


class ExtensionPoint(Generic[T_Extension]):
    """Extension point for registering and managing extensions.

    This class provides functionality for:
    - Extension registration and discovery
    - Extension lifecycle management
    - Extension dependency resolution
    - Extension configuration validation
    """

    def __init__(self, name: str, extension_type: Type[T_Extension]) -> None:
        """Initialize extension point.

        Args:
            name: Extension point name
            extension_type: Type of extensions this point accepts
        """
        self._name = name
        self._extension_type = extension_type
        self._extensions: Dict[str, T_Extension] = {}
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        """Get extension point name."""
        return self._name

    @property
    def extension_type(self) -> Type[T_Extension]:
        """Get extension type."""
        return self._extension_type

    async def register_extension(self, extension: T_Extension) -> None:
        """Register an extension.

        Args:
            extension: Extension to register

        Raises:
            ValueError: If extension is invalid
            ExtensionError: If registration fails
        """
        if not isinstance(extension, (self._extension_type, ExtensionProtocol)):
            raise ValueError(
                f"Extension must be of type {self._extension_type.__name__} "
                "and implement ExtensionProtocol"
            )

        async with self._lock:
            if extension.metadata.name in self._extensions:
                raise ExtensionError(
                    f"Extension {extension.metadata.name} already registered"
                )

            # Initialize extension
            try:
                await extension.initialize()
                self._extensions[extension.metadata.name] = extension
                logger.info(
                    f"Registered extension {extension.metadata.name} "
                    f"version {extension.metadata.version}"
                )
            except Exception as e:
                raise ExtensionError(f"Failed to register extension: {e}") from e

    async def unregister_extension(self, name: str) -> None:
        """Unregister an extension.

        Args:
            name: Extension name

        Raises:
            ExtensionError: If unregistration fails
        """
        async with self._lock:
            if name not in self._extensions:
                raise ExtensionError(f"Extension {name} not registered")

            # Clean up extension
            extension = self._extensions[name]
            try:
                await extension.cleanup()
                del self._extensions[name]
                logger.info(f"Unregistered extension {name}")
            except Exception as e:
                raise ExtensionError(f"Failed to unregister extension: {e}") from e

    def get_extension(self, name: str) -> Optional[T_Extension]:
        """Get an extension by name.

        Args:
            name: Extension name

        Returns:
            Extension if found, None otherwise
        """
        return self._extensions.get(name)

    def get_extensions(self) -> List[T_Extension]:
        """Get all registered extensions.

        Returns:
            List of registered extensions
        """
        return list(self._extensions.values())

    async def cleanup(self) -> None:
        """Clean up all registered extensions."""
        async with self._lock:
            for extension in self._extensions.values():
                try:
                    await extension.cleanup()
                except Exception as e:
                    logger.error(f"Failed to clean up extension: {e}")
            self._extensions.clear()
