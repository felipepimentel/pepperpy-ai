"""Text chunker implementation."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

ConfigT = TypeVar("ConfigT")


class BaseChunker(Generic[ConfigT], ABC):
    """Base text chunker implementation."""

    def __init__(self, config: ConfigT) -> None:
        """Initialize chunker.

        Args:
            config: Chunker configuration
        """
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if chunker is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize chunker."""
        if not self._initialized:
            await self._setup()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup chunker resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure chunker is initialized."""
        if not self._initialized:
            raise RuntimeError("Chunker not initialized")

    @abstractmethod
    async def _setup(self) -> None:
        """Setup chunker resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown chunker resources."""
        pass

    @abstractmethod
    async def chunk(self, text: str, **kwargs: Any) -> list[str]:
        """Split text into chunks.

        Args:
            text: Text to chunk
            **kwargs: Additional arguments

        Returns:
            List of text chunks

        Raises:
            ChunkingError: If chunking fails
            RuntimeError: If chunker not initialized
        """
        pass

    @abstractmethod
    async def merge(self, chunks: list[str], **kwargs: Any) -> str:
        """Merge chunks back into text.

        Args:
            chunks: Text chunks to merge
            **kwargs: Additional arguments

        Returns:
            Merged text

        Raises:
            ChunkingError: If merging fails
            RuntimeError: If chunker not initialized
        """
        pass

    @abstractmethod
    async def get_metadata(self) -> dict[str, Any]:
        """Get chunker metadata.

        Returns:
            Chunker metadata

        Raises:
            RuntimeError: If chunker not initialized
        """
        pass
