"""Text document loader implementation.

This module provides functionality for loading text documents.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.errors import DocumentLoadError
from pepperpy.rag.document.loaders.base import BaseDocumentLoader
from pepperpy.rag.storage.types import Document


class TextLoader(BaseDocumentLoader):
    """Text document loader.

    This loader handles plain text documents, with support for chunking
    based on size and overlap.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding: str = "utf-8",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the text loader.

        Args:
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters to overlap between chunks.
            encoding: Text encoding to use when reading files.
            metadata: Optional metadata to associate with loaded documents.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(metadata=metadata, **kwargs)
        self.chunk_size = max(1, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, chunk_size - 1))
        self.encoding = encoding

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: Text to split into chunks.

        Returns:
            List of text chunks.
        """
        # Handle empty or short text
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk of specified size
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at paragraph/sentence
            if end < len(text):
                # Try to break at paragraph
                paragraph_break = text.rfind("\n\n", start, end)
                if paragraph_break != -1 and paragraph_break > start:
                    end = paragraph_break

                # Try to break at newline
                elif (
                    newline := text.rfind("\n", start, end)
                ) != -1 and newline > start:
                    end = newline

                # Try to break at sentence
                elif (period := text.rfind(". ", start, end)) != -1 and period > start:
                    end = period + 1

                # Try to break at space
                elif (space := text.rfind(" ", start, end)) != -1 and space > start:
                    end = space

            # Add chunk
            chunks.append(text[start:end].strip())

            # Move start position, accounting for overlap
            start = end - self.chunk_overlap

        return chunks

    async def _load_from_file(
        self,
        file_path: Union[str, Path],
        **kwargs: Any,
    ) -> List[Document]:
        """Load text from a file.

        Args:
            file_path: Path to the text file.
            **kwargs: Additional arguments.

        Returns:
            List containing the loaded document.

        Raises:
            DocumentLoadError: If file reading fails.
        """
        try:
            # Read file asynchronously
            path = Path(file_path)
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: path.read_text(encoding=self.encoding),
            )

            # Create document from content
            return await self._load_from_string(content, file_path=path, **kwargs)

        except Exception as e:
            raise DocumentLoadError(f"Error reading text file: {str(e)}") from e

    async def _load_from_string(
        self,
        content: str,
        **kwargs: Any,
    ) -> List[Document]:
        """Load text from a string.

        Args:
            content: Text content to load.
            **kwargs: Additional arguments.

        Returns:
            List containing the loaded document.

        Raises:
            DocumentLoadError: If text processing fails.
        """
        try:
            # Get source file path if provided
            file_path = kwargs.get("file_path")
            source = str(file_path) if file_path else None

            # Split text into chunks
            chunk_texts = self._chunk_text(content)

            # Create document chunks
            chunks = []
            for i, text in enumerate(chunk_texts):
                chunk = Document.Chunk(
                    content=text,
                    metadata={
                        "chunk_index": i,
                        "total_chunks": len(chunk_texts),
                    },
                )
                chunks.append(chunk)

            # Create document
            if not chunks:
                return []

            doc = Document(
                chunks=chunks,
                metadata={
                    "source": source,
                    "content_type": "text/plain",
                    "encoding": self.encoding,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                }
                if source
                else None,
            )

            return [doc]

        except Exception as e:
            raise DocumentLoadError(f"Error processing text: {str(e)}") from e
