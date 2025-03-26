"""Recursive character n-gram text chunking."""

from typing import Any, Dict, List, Optional

from pepperpy.rag.chunking.base import (
    Chunk,
    ChunkingError,
    ChunkingOptions,
    TextChunker,
)


class RecursiveCharNGramChunker(TextChunker):
    """Chunker that uses recursive character n-grams.

    This chunker splits text into overlapping character n-grams recursively:
    1. First splits into large chunks based on natural boundaries
    2. Then recursively splits chunks that are too large
    3. Maintains overlap between chunks to preserve context
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Initialize recursive chunker.

        Args:
            config: Optional configuration
            **kwargs: Additional configuration options
        """
        super().__init__(name="recursive", config=config, **kwargs)

    async def _initialize(self) -> None:
        """Initialize the chunker."""
        pass

    async def _cleanup(self) -> None:
        """Clean up resources."""
        pass

    def _find_split_point(self, text: str, target_size: int) -> int:
        """Find optimal split point in text.

        Looks for natural boundaries like:
        1. Paragraph breaks
        2. Sentence endings
        3. Word boundaries

        Args:
            text: Text to split
            target_size: Target size for split point

        Returns:
            Index of split point
        """
        # Look for paragraph break near target
        search_range = slice(
            max(0, target_size - 100), min(len(text), target_size + 100)
        )
        text_range = text[search_range]

        # Try paragraph break
        for pattern in ["\n\n", "\r\n\r\n"]:
            if pattern in text_range:
                return search_range.start + text_range.index(pattern) + len(pattern)

        # Try sentence ending
        for pattern in [".", "!", "?"]:
            if pattern in text_range:
                return search_range.start + text_range.rindex(pattern) + 1

        # Fall back to word boundary
        for pattern in [" ", "\n", "\t"]:
            if pattern in text_range:
                return search_range.start + text_range.rindex(pattern) + 1

        # Last resort - split at target size
        return target_size

    def _split_chunk(
        self, text: str, start: int, options: ChunkingOptions
    ) -> List[Chunk]:
        """Split text into chunks recursively.

        Args:
            text: Text to split
            start: Start position in original text
            options: Chunking options

        Returns:
            List of chunks
        """
        chunks = []

        # Base case - text is within size constraints
        if len(text) >= options.min_chunk_size and len(text) <= options.max_chunk_size:
            chunks.append(
                Chunk(
                    text=text,
                    start=start,
                    end=start + len(text),
                    metadata={"type": "recursive"},
                )
            )
            return chunks

        # Recursive case - split text and process each part
        split_point = self._find_split_point(text, target_size=options.chunk_size)

        # Process first part
        first_part = text[:split_point]
        if first_part:
            chunks.extend(self._split_chunk(first_part, start, options))

        # Process second part with overlap
        if split_point < len(text):
            overlap_start = max(0, split_point - options.chunk_overlap)
            second_part = text[overlap_start:]
            if second_part:
                chunks.extend(
                    self._split_chunk(second_part, start + overlap_start, options)
                )

        return chunks

    async def chunk_text(
        self, text: str, options: Optional[ChunkingOptions] = None
    ) -> List[Chunk]:
        """Split text into overlapping chunks recursively.

        Args:
            text: Text to split
            options: Optional chunking options

        Returns:
            List of chunks

        Raises:
            ChunkingError: If chunking fails
        """
        try:
            options = options or ChunkingOptions()
            return self._split_chunk(text, 0, options)

        except Exception as e:
            raise ChunkingError(f"Failed to chunk text: {e}")

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
        try:
            # Sort chunks by start position
            sorted_chunks = sorted(chunks, key=lambda x: x.start)

            # Merge chunks, removing overlaps
            merged = []
            last_end = 0

            for chunk in sorted_chunks:
                # Skip if chunk is completely overlapped
                if chunk.end <= last_end:
                    continue

                # Add non-overlapping portion
                if chunk.start < last_end:
                    merged.append(chunk.text[last_end - chunk.start :])
                else:
                    merged.append(chunk.text)

                last_end = chunk.end

            return "".join(merged)

        except Exception as e:
            raise ChunkingError(f"Failed to merge chunks: {e}")
