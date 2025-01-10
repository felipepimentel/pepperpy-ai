"""Text processor implementation."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

ConfigT = TypeVar("ConfigT")


class BaseProcessor(Generic[ConfigT], ABC):
    """Base text processor implementation."""

    def __init__(self, config: ConfigT) -> None:
        """Initialize processor.

        Args:
            config: Processor configuration
        """
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if processor is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize processor."""
        if not self._initialized:
            await self._setup()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup processor resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure processor is initialized."""
        if not self._initialized:
            raise RuntimeError("Processor not initialized")

    @abstractmethod
    async def _setup(self) -> None:
        """Setup processor resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown processor resources."""
        pass

    @abstractmethod
    async def process(self, text: str, **kwargs: Any) -> str:
        """Process text.

        Args:
            text: Text to process
            **kwargs: Additional arguments

        Returns:
            Processed text

        Raises:
            ProcessingError: If processing fails
            ValidationError: If validation fails
            RuntimeError: If processor not initialized
        """
        pass

    @abstractmethod
    async def validate(self, text: str) -> None:
        """Validate text.

        Args:
            text: Text to validate

        Raises:
            ValidationError: If validation fails
            RuntimeError: If processor not initialized
        """
        pass

    @abstractmethod
    async def get_metadata(self) -> dict[str, Any]:
        """Get processor metadata.

        Returns:
            Processor metadata

        Raises:
            RuntimeError: If processor not initialized
        """
        pass
