"""Base interfaces for text chunking in the RAG pipeline."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.core.base import BaseProvider


@dataclass
class Chunk:
    """A chunk of text with metadata.

    Attributes:
        text: The chunk text content
        start: Start position in original text
        end: End position in original text
        metadata: Additional metadata about the chunk
    """

    text: str
    start: int
    end: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkingOptions:
    """Options for text chunking.

    Attributes:
        chunk_size: Target size for chunks (implementation specific)
        chunk_overlap: How much chunks should overlap (implementation specific)
        min_chunk_size: Minimum chunk size
        max_chunk_size: Maximum chunk size
        additional_options: Additional chunker-specific options
    """

    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    max_chunk_size: int = 1000
    additional_options: Dict[str, Any] = field(default_factory=dict)


class ChunkingError(Exception):
    """Error raised during text chunking."""

    pass


class TextChunker(BaseProvider):
    """Base class for text chunkers."""

    @abstractmethod
    async def chunk_text(
        self, text: str, options: Optional[ChunkingOptions] = None
    ) -> List[Chunk]:
        """Split text into chunks.

        Args:
            text: Text to split into chunks
            options: Optional chunking options

        Returns:
            List of text chunks

        Raises:
            ChunkingError: If chunking fails
        """
        pass

    @abstractmethod
    async def merge_chunks(
        self, chunks: List[Chunk], options: Optional[ChunkingOptions] = None
    ) -> str:
        """Merge chunks back into text.

        Args:
            chunks: Chunks to merge
            options: Optional chunking options

        Returns:
            Merged text

        Raises:
            ChunkingError: If merging fails
        """
        pass
