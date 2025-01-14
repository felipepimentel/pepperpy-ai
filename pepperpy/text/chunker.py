"""Text chunker module."""

from abc import ABC, abstractmethod
from typing import TypedDict


class ChunkerParams(TypedDict, total=False):
    """Text chunker parameters."""

    chunk_size: int | None
    chunk_overlap: int | None
    min_chunk_size: int | None
    max_chunk_size: int | None
    normalize: bool | None


class BaseTextChunker(ABC):
    """Base text chunker implementation."""

    @abstractmethod
    async def chunk(self, text: str, **kwargs: ChunkerParams) -> list[str]:
        """Split text into chunks.

        Args:
            text: Text to split into chunks.
            **kwargs: Chunking parameters.

        Returns:
            list[str]: List of text chunks.
        """
        pass

    @abstractmethod
    async def merge(self, chunks: list[str], **kwargs: ChunkerParams) -> str:
        """Merge chunks back into text.

        Args:
            chunks: List of text chunks to merge.
            **kwargs: Merging parameters.

        Returns:
            str: Merged text.
        """
        pass
