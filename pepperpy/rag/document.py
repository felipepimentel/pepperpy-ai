"""Document module for RAG.

This module provides functionality for working with documents in RAG,
including loading, processing, and transformation.
"""

from typing import Any, List, Optional

from pepperpy.core.errors import PepperPyError
from pepperpy.rag.interfaces import DocumentLoader, DocumentProcessor
from pepperpy.rag.models import (
    ChunkingConfig,
    ChunkingStrategy,
    Document,
    DocumentChunk,
    Metadata,
)


class TextLoader(DocumentLoader):
    """Loader for text documents.

    This loader loads text documents from various sources, including
    files, strings, and URLs.
    """

    async def load(self, source: str, **kwargs: Any) -> Document:
        """Load a text document from a source.

        Args:
            source: The source to load the document from
            **kwargs: Additional arguments for loading

        Returns:
            The loaded document

        Raises:
            ValidationError: If the source is invalid
            PepperPyError: If loading fails
        """
        # Implementation will depend on whether source is a file path or text content
        content = ""
        metadata = Metadata()

        if source.startswith("http://") or source.startswith("https://"):
            # URL source
            # This would fetch content from the URL
            metadata.source = source
            raise NotImplementedError("URL loading not implemented yet")

        elif kwargs.get("is_content", False):
            # Direct content source
            content = source

        else:
            # File path source
            try:
                with open(source, "r", encoding="utf-8") as file:
                    content = file.read()
                metadata.source = source
            except Exception as e:
                raise PepperPyError(f"Failed to load text document: {e}")

        # Create and return the document
        return Document(content=content, metadata=metadata)


class TextChunker(DocumentProcessor):
    """Processor for chunking text documents.

    This processor splits documents into chunks based on various strategies.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        """Initialize the text chunker.

        Args:
            config: The chunking configuration
        """
        self.config = config or ChunkingConfig()

    async def process(self, document: Document) -> List[DocumentChunk]:
        """Process a document by chunking it.

        Args:
            document: The document to process

        Returns:
            The processed document chunks

        Raises:
            ValidationError: If the document is invalid
            PepperPyError: If processing fails
        """
        chunks: List[DocumentChunk] = []
        content = document.content
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        # Simple implementation of fixed-size chunking
        if self.config.strategy == ChunkingStrategy.FIXED_SIZE:
            # Split text into chunks of specified size with overlap
            if not content:
                return chunks

            start = 0
            chunk_index = 0

            while start < len(content):
                # Determine end position
                end = min(start + chunk_size, len(content))

                # If we're not at the end and respect_sentence_boundaries is True,
                # try to find a sentence boundary
                if end < len(content) and self.config.respect_sentence_boundaries:
                    # Look for period, question mark, or exclamation point followed by space
                    for i in range(end - 1, max(start, end - 100), -1):
                        if content[i] in ".!?" and (
                            i + 1 >= len(content) or content[i + 1].isspace()
                        ):
                            end = i + 1
                            break

                # Extract chunk text
                chunk_text = content[start:end]

                # Create chunk
                chunk = DocumentChunk(
                    content=chunk_text,
                    metadata=document.metadata,
                    document_id=document.id,
                    chunk_index=chunk_index,
                )

                chunks.append(chunk)

                # Move to next chunk with overlap
                start = end - overlap if end < len(content) else len(content)
                chunk_index += 1

        # Other strategies would be implemented here

        return chunks


class TextCleaner(DocumentProcessor):
    """Processor for cleaning text documents.

    This processor cleans text documents by removing unwanted content
    and normalizing formatting.
    """

    async def process(self, document: Document) -> Document:
        """Process a document by cleaning its text.

        Args:
            document: The document to process

        Returns:
            The processed document

        Raises:
            ValidationError: If the document is invalid
            PepperPyError: If processing fails
        """
        if not document.content:
            return document

        content = document.content

        # Basic text cleaning
        # Remove excessive whitespace
        content = " ".join(content.split())

        # Create a new document with cleaned content
        return Document(content=content, metadata=document.metadata, id=document.id)


async def load_text_document(source: str, is_content: bool = False) -> Document:
    """Load a text document.

    This is a convenience function that creates a TextLoader and loads
    a document from the specified source.

    Args:
        source: The source to load the document from
        is_content: Whether the source is the content itself

    Returns:
        The loaded document
    """
    loader = TextLoader()
    return await loader.load(source, is_content=is_content)


async def chunk_document(
    document: Document, chunk_size: int = 1000, overlap: int = 200
) -> List[DocumentChunk]:
    """Chunk a document.

    This is a convenience function that creates a TextChunker and
    processes a document to create chunks.

    Args:
        document: The document to chunk
        chunk_size: The chunk size
        overlap: The overlap between chunks

    Returns:
        The document chunks
    """
    config = ChunkingConfig(chunk_size=chunk_size, chunk_overlap=overlap)
    chunker = TextChunker(config=config)
    return await chunker.process(document)
