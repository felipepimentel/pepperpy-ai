"""
PepperPy Tool Base Module.

Base interfaces and abstractions for tool functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from pepperpy.core.errors import PepperpyError


class ToolError(PepperpyError):
    """Base error for tool operations."""

    pass


class ToolProviderError(ToolError):
    """Error raised by tool providers."""

    pass


class ToolConfigError(ToolProviderError):
    """Error related to tool configuration."""

    pass


class ToolProvider(Protocol):
    """Protocol defining tool provider interface."""

    async def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a tool command.

        Args:
            command: Command to execute
            **kwargs: Additional command-specific parameters

        Returns:
            Command result
        """
        ...

    async def get_capabilities(self) -> list[str]:
        """Get the tool's capabilities.

        Returns:
            List of capability strings
        """
        ...

    async def validate_config(self) -> bool:
        """Validate the tool configuration.

        Returns:
            True if configuration is valid
        """
        ...


class BaseToolProvider(ABC):
    """Base implementation for tool providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize base tool provider.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the tool provider.

        Implementations should set self.initialized to True when complete.
        """
        self.initialized = True

    @abstractmethod
    async def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a tool command.

        Args:
            command: Command to execute
            **kwargs: Additional command-specific parameters

        Returns:
            Command result
        """
        if not self.initialized:
            await self.initialize()
        raise ToolProviderError("Command execution not implemented")

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """Get the tool's capabilities.

        Returns:
            List of capability strings
        """
        if not self.initialized:
            await self.initialize()
        return []

    async def validate_config(self) -> bool:
        """Validate the tool configuration.

        Returns:
            True if configuration is valid
        """
        if not self.initialized:
            await self.initialize()
        # Base implementation just returns True
        # Subclasses should override this with actual validation
        return True
