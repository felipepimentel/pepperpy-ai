"""Common type definitions for PepperPy.

This module provides common type definitions that are shared across different
modules in the PepperPy framework. By centralizing these definitions, we ensure
consistency and avoid duplication.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    TypeVar,
    runtime_checkable,
)

# Type variables for generic types
T = TypeVar("T")
U = TypeVar("U")

# -----------------------------------------------------------------------------
# Metadata Structures
# -----------------------------------------------------------------------------


@dataclass
class Metadata:
    """Consolidated metadata structure for documents and resources.

    Attributes:
        source: The source of the document or resource
        created_at: The creation time
        updated_at: The last update time
        author: The author
        title: The title
        tags: Tags for categorization
        custom: Custom metadata for extensibility
    """

    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
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
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
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

        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                updated_at = None

        return cls(
            source=data.get("source"),
            created_at=created_at,
            updated_at=updated_at,
            author=data.get("author"),
            title=data.get("title"),
            tags=set(data.get("tags", [])),
            custom=data.get("custom", {}),
        )


# -----------------------------------------------------------------------------
# Document Structures
# -----------------------------------------------------------------------------


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have an identifier.

    This protocol defines the interface for objects that have a unique identifier.
    """

    @property
    def id(self) -> str:
        """Get the identifier.

        Returns:
            The identifier
        """
        ...


@dataclass
class Document:
    """Consolidated document structure.

    Attributes:
        content: The content of the document
        metadata: Metadata for the document
        id: The ID of the document
    """

    content: str
    metadata: Metadata = field(default_factory=Metadata)
    id: str = field(default="")

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


# -----------------------------------------------------------------------------
# Result Structures
# -----------------------------------------------------------------------------


@dataclass
class Result(Generic[T]):
    """Consolidated result structure for operation results.

    Attributes:
        success: Whether the operation was successful
        data: The data returned by the operation
        error: The error that occurred, if any
        metadata: Additional metadata for the result
    """

    success: bool = True
    data: Optional[T] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            The result as a dictionary
        """
        return {
            "success": self.success,
            "data": self.data,
            "error": str(self.error) if self.error else None,
            "metadata": self.metadata,
        }


# -----------------------------------------------------------------------------
# Context Structures
# -----------------------------------------------------------------------------


@dataclass
class Context:
    """Consolidated context structure for operations.

    Attributes:
        data: The context data
        metadata: Metadata for the context
    """

    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context.

        Args:
            key: The key to get
            default: The default value if the key is not found

        Returns:
            The value for the key, or the default if not found
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context.

        Args:
            key: The key to set
            value: The value to set
        """
        self.data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to a dictionary.

        Returns:
            The context as a dictionary
        """
        return {
            "data": self.data,
            "metadata": self.metadata,
        }


# -----------------------------------------------------------------------------
# Vector Embedding Structures
# -----------------------------------------------------------------------------


@dataclass
class VectorEmbedding:
    """A vector embedding for a document chunk.

    Attributes:
        vector: The vector embedding
        document_id: The ID of the document this embedding belongs to
        chunk_id: The ID of the document chunk this embedding belongs to
        metadata: Additional metadata for the embedding
    """

    vector: List[float]
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the vector embedding to a dictionary.

        Returns:
            The vector embedding as a dictionary
        """
        return {
            "vector": self.vector,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorEmbedding":
        """Create a vector embedding from a dictionary.

        Args:
            data: The dictionary to create the vector embedding from

        Returns:
            The created vector embedding
        """
        return cls(
            vector=data.get("vector", []),
            document_id=data.get("document_id", ""),
            chunk_id=data.get("chunk_id", ""),
            metadata=data.get("metadata", {}),
        )
