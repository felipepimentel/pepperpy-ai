"""Text document processor.

This module provides functionality for processing text documents.
"""

from typing import Dict, List, Optional

from pepperpy.rag.document.core import Document, DocumentChunk
from pepperpy.rag.errors import DocumentProcessError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class TextProcessor:
    """Processor for text documents.

    This processor processes text documents by splitting them into chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n",
        metadata: Optional[Dict[str, str]] = None,
    ):
        """Initialize a text processor.

        Args:
            chunk_size: The maximum size of each chunk in characters
            chunk_overlap: The number of characters to overlap between chunks
            separator: The separator to use when splitting text
            metadata: Additional metadata to add to the chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self.metadata = metadata or {}

    async def process(self, document: Document) -> List[DocumentChunk]:
        """Process a document.

        Args:
            document: The document to process

        Returns:
            The processed document chunks

        Raises:
            DocumentProcessError: If there is an error processing the document
        """
        try:
            # Get the document content
            content = document.content

            # Split the document into chunks
            chunks = self._split_text(content)

            # Create document chunks
            document_chunks = []

            for i, chunk in enumerate(chunks):
                # Create chunk metadata
                chunk_metadata = {
                    **document.metadata.to_dict(),
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    **self.metadata,
                }

                # Create the document chunk
                document_chunk = DocumentChunk(
                    content=chunk,
                    metadata=chunk_metadata,
                    document_id=document.id,
                )

                document_chunks.append(document_chunk)

            return document_chunks
        except Exception as e:
            raise DocumentProcessError(f"Error processing text document: {e}")

    async def process_batch(self, documents: List[Document]) -> List[DocumentChunk]:
        """Process a batch of documents.

        Args:
            documents: The documents to process

        Returns:
            The processed document chunks

        Raises:
            DocumentProcessError: If there is an error processing the documents
        """
        chunks = []

        for document in documents:
            try:
                document_chunks = await self.process(document)
                chunks.extend(document_chunks)
            except Exception as e:
                logger.error(f"Error processing document {document.id}: {e}")

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: The text to split

        Returns:
            The chunks
        """
        # Split the text by separator
        segments = text.split(self.separator)

        chunks = []
        current_chunk = ""

        for segment in segments:
            # If adding the segment would exceed the chunk size, start a new chunk
            if (
                len(current_chunk) + len(segment) + len(self.separator)
                > self.chunk_size
                and current_chunk
            ):
                chunks.append(current_chunk)

                # Start a new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    # Get the last part of the current chunk for overlap
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:]
                else:
                    current_chunk = ""

            # Add the segment to the current chunk
            if current_chunk:
                current_chunk += self.separator + segment
            else:
                current_chunk = segment

        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
