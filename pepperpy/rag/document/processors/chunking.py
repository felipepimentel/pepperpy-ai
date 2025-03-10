"""Document chunking processor module.

This module provides functionality for splitting documents into smaller chunks.
"""

from typing import Any, List, Optional, Union

from pepperpy.errors import DocumentProcessError
from pepperpy.rag.document.processors.base import BaseDocumentProcessor
from pepperpy.rag.document.types import Document, DocumentChunk


class ChunkingProcessor(BaseDocumentProcessor):
    """Document chunking processor.

    This processor splits documents into smaller chunks based on various strategies:
    - Fixed size chunks with optional overlap
    - Split by separator (newlines, paragraphs, etc.)
    - Split by semantic units (sentences, paragraphs)
    - Preserve chunk boundaries at natural breaks
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: int = 0,
        split_by: str = "size",
        separator: Optional[str] = None,
        preserve_boundaries: bool = True,
        min_chunk_size: Optional[int] = None,
        max_chunk_size: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the chunking processor.

        Args:
            chunk_size: Size of each chunk (in characters or tokens).
            chunk_overlap: Number of characters/tokens to overlap between chunks.
            split_by: Chunking strategy ('size', 'separator', 'sentence', 'paragraph').
            separator: Custom separator for splitting (used if split_by='separator').
            preserve_boundaries: Whether to preserve natural text boundaries.
            min_chunk_size: Minimum chunk size (for variable-size chunks).
            max_chunk_size: Maximum chunk size (for variable-size chunks).
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.chunk_size = chunk_size
        self.chunk_overlap = min(chunk_overlap, chunk_size or 0)
        self.split_by = split_by
        self.separator = separator
        self.preserve_boundaries = preserve_boundaries
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size or chunk_size

        # Validate configuration
        if split_by not in ["size", "separator", "sentence", "paragraph"]:
            raise ValueError(f"Invalid split_by value: {split_by}")
        if split_by == "separator" and not separator:
            raise ValueError("Separator must be provided when split_by='separator'")

    def _find_break_point(self, text: str, end: int) -> int:
        """Find a natural break point in text near the specified position.

        Args:
            text: Text to search for break point.
            end: Target position for break point.

        Returns:
            Actual break point position.
        """
        if not self.preserve_boundaries:
            return end

        # Try to break at paragraph
        if end < len(text):
            para_break = text[:end].rfind("\n\n")
            if para_break != -1 and para_break > end * 0.5:
                return para_break + 2

        # Try to break at sentence
        sentence_breaks = [". ", "! ", "? ", ".\n", "!\n", "?\n"]
        for break_char in sentence_breaks:
            sentence_break = text[:end].rfind(break_char)
            if sentence_break != -1 and sentence_break > end * 0.5:
                return sentence_break + len(break_char)

        # Try to break at word boundary
        space_break = text[:end].rfind(" ")
        if space_break != -1:
            return space_break + 1

        return end

    def _split_by_size(self, text: str) -> List[str]:
        """Split text into chunks of specified size.

        Args:
            text: Text to split.

        Returns:
            List of text chunks.
        """
        if not self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            # Get chunk of specified size
            end = start + self.chunk_size
            if end > text_len:
                end = text_len

            # Find natural break point
            break_point = self._find_break_point(text, end)
            chunk = text[start:break_point]

            # Ensure chunk meets size constraints
            if (
                self.min_chunk_size
                and len(chunk) < self.min_chunk_size
                and len(chunks) > 0
            ):
                # Append to previous chunk if too small
                chunks[-1] = chunks[-1] + chunk
            else:
                chunks.append(chunk)

            # Move start position
            start = break_point - self.chunk_overlap

        return chunks

    def _split_by_separator(self, text: str) -> List[str]:
        """Split text by custom separator.

        Args:
            text: Text to split.

        Returns:
            List of text chunks.
        """
        if not self.separator:
            return [text]

        # Split by separator
        parts = text.split(self.separator)
        chunks = []
        current_chunk = []
        current_size = 0

        for part in parts:
            part_size = len(part)

            # Check if adding this part would exceed max size
            if (
                self.max_chunk_size
                and current_size + part_size > self.max_chunk_size
                and current_chunk
            ):
                # Store current chunk and start new one
                chunks.append(self.separator.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(part)
            current_size += part_size

        # Add final chunk
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return chunks

    def _split_by_semantic(self, text: str) -> List[str]:
        """Split text by semantic units (sentences or paragraphs).

        Args:
            text: Text to split.

        Returns:
            List of text chunks.
        """
        if self.split_by == "paragraph":
            separator = "\n\n"
        else:  # sentence
            text = text.replace("\n", " ")
            separator = ". "

        return self._split_by_separator(text)

    async def process(
        self,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> Union[Document, List[Document]]:
        """Process one or more documents by splitting them into chunks.

        Args:
            documents: A single document or list of documents to process.
            **kwargs: Additional keyword arguments for processing.

        Returns:
            The processed document(s) with content split into chunks.

        Raises:
            DocumentProcessError: If processing fails.
        """
        try:
            if isinstance(documents, Document):
                documents = [documents]

            processed_docs = []
            for doc in documents:
                # Process each chunk
                processed_chunks = []
                for chunk in doc.chunks:
                    # Split content based on strategy
                    if self.split_by in ["sentence", "paragraph"]:
                        parts = self._split_by_semantic(chunk.content)
                    elif self.split_by == "separator":
                        parts = self._split_by_separator(chunk.content)
                    else:  # size
                        parts = self._split_by_size(chunk.content)

                    # Create new chunks
                    for i, part in enumerate(parts):
                        processed_chunk = DocumentChunk(
                            content=part.strip(),
                            metadata={
                                **(chunk.metadata or {}),
                                "chunk_index": i,
                                "chunk_size": len(part),
                                "original_chunk_index": chunk.metadata.get(
                                    "chunk_index", 0
                                )
                                if chunk.metadata
                                else 0,
                            },
                        )
                        processed_chunks.append(processed_chunk)

                # Create processed document
                processed_doc = Document(
                    chunks=processed_chunks,
                    metadata={
                        **(doc.metadata or {}),
                        "chunking_strategy": self.split_by,
                        "chunk_count": len(processed_chunks),
                    },
                )
                processed_docs.append(processed_doc)

            return processed_docs[0] if len(processed_docs) == 1 else processed_docs

        except Exception as e:
            raise DocumentProcessError(
                f"Error splitting document into chunks: {str(e)}"
            ) from e
