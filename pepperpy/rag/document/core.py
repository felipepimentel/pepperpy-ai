"""Core functionality for document processing in RAG.

This module provides the core functionality for document processing in RAG,
including document representation, loading, and processing.
"""

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from pepperpy.interfaces import Identifiable
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


@dataclass
class Metadata:
    """Metadata for a document.

    Attributes:
        source: The source of the document
        created_at: The creation time of the document
        author: The author of the document
        title: The title of the document
        tags: Tags for the document
        custom: Custom metadata
    """

    source: Optional[str] = None
    created_at: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metadata to a dictionary.

        Returns:
            The metadata as a dictionary
        """
        return {
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "author": self.author,
            "title": self.title,
            "tags": list(self.tags),
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        """Create metadata from a dictionary.

        Args:
            data: The dictionary to create the metadata from

        Returns:
            The created metadata
        """
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None

        return cls(
            source=data.get("source"),
            created_at=created_at,
            author=data.get("author"),
            title=data.get("title"),
            tags=set(data.get("tags", [])),
            custom=data.get("custom", {}),
        )


@dataclass
class Document(Identifiable):
    """A document for RAG.

    Attributes:
        content: The content of the document
        metadata: Metadata for the document
        id: The ID of the document
    """

    content: str
    metadata: Metadata = field(default_factory=Metadata)
    id: str = field(default="")

    def __post_init__(self) -> None:
        """Initialize the document."""
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate an ID for the document.

        Returns:
            The generated ID
        """
        # Create a hash of the content and metadata
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        metadata_hash = hashlib.sha256(
            json.dumps(self.metadata.to_dict(), sort_keys=True).encode()
        ).hexdigest()

        return f"{content_hash[:8]}-{metadata_hash[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the document to a dictionary.

        Returns:
            The document as a dictionary
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a document from a dictionary.

        Args:
            data: The dictionary to create the document from

        Returns:
            The created document
        """
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=Metadata.from_dict(data.get("metadata", {})),
        )


@dataclass
class DocumentChunk(Identifiable):
    """A chunk of a document for RAG.

    Attributes:
        content: The content of the chunk
        metadata: Metadata for the chunk
        document_id: The ID of the document this chunk belongs to
        chunk_index: The index of this chunk in the document
        id: The ID of the chunk
    """

    content: str
    metadata: Metadata
    document_id: str
    chunk_index: int = 0
    id: str = field(default="")

    def __post_init__(self) -> None:
        """Initialize the document chunk."""
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate an ID for the document chunk.

        Returns:
            The generated ID
        """
        # Create a hash of the content, document ID, and chunk index
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()

        return f"{self.document_id}-{self.chunk_index}-{content_hash[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the document chunk to a dictionary.

        Returns:
            The document chunk as a dictionary
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        """Create a document chunk from a dictionary.

        Args:
            data: The dictionary to create the document chunk from

        Returns:
            The created document chunk
        """
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            metadata=Metadata.from_dict(data.get("metadata", {})),
            document_id=data.get("document_id", ""),
            chunk_index=data.get("chunk_index", 0),
        )


class DocumentLoader(ABC):
    """Base class for document loaders.

    Document loaders are responsible for loading documents from various sources,
    such as files, URLs, or databases.
    """

    @abstractmethod
    async def load(self, source: str) -> Document:
        """Load a document from a source.

        Args:
            source: The source to load the document from

        Returns:
            The loaded document

        Raises:
            DocumentLoadError: If there is an error loading the document
        """
        pass


class DocumentProcessor(ABC):
    """Base class for document processors.

    Document processors are responsible for processing documents, such as
    splitting them into chunks, extracting metadata, or transforming the content.
    """

    @abstractmethod
    async def process(self, document: Document) -> List[DocumentChunk]:
        """Process a document.

        Args:
            document: The document to process

        Returns:
            The processed document chunks

        Raises:
            DocumentProcessError: If there is an error processing the document
        """
        pass


class DocumentStore(ABC):
    """Base class for document stores.

    Document stores are responsible for storing and retrieving documents and
    document chunks.
    """

    @abstractmethod
    async def add_document(self, document: Document) -> None:
        """Add a document to the store.

        Args:
            document: The document to add

        Raises:
            DocumentError: If there is an error adding the document
        """
        pass

    @abstractmethod
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the store.

        Args:
            chunks: The document chunks to add

        Raises:
            DocumentError: If there is an error adding the document chunks
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document from the store.

        Args:
            document_id: The ID of the document to get

        Returns:
            The document, or None if it doesn't exist

        Raises:
            DocumentError: If there is an error getting the document
        """
        pass

    @abstractmethod
    async def get_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get document chunks from the store.

        Args:
            document_id: The ID of the document to get chunks for

        Returns:
            The document chunks

        Raises:
            DocumentError: If there is an error getting the document chunks
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        """Delete a document from the store.

        Args:
            document_id: The ID of the document to delete

        Raises:
            DocumentError: If there is an error deleting the document
        """
        pass

    @abstractmethod
    async def delete_chunks(self, document_id: str) -> None:
        """Delete document chunks from the store.

        Args:
            document_id: The ID of the document to delete chunks for

        Raises:
            DocumentError: If there is an error deleting the document chunks
        """
        pass

    @abstractmethod
    async def list_documents(self) -> List[Document]:
        """List all documents in the store.

        Returns:
            The documents

        Raises:
            DocumentError: If there is an error listing the documents
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the store.

        Raises:
            DocumentError: If there is an error clearing the store
        """
        pass
