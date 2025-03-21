"""Document module for RAG functionality.

This module provides document representation and processing for RAG.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """Document representation for RAG.

    This class represents a document in the RAG system, including its content,
    metadata, and embeddings.

    Args:
        content: Document content
        metadata: Optional document metadata
        embeddings: Optional document embeddings
        id: Optional document ID
        created_at: Document creation timestamp
    """

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize document after creation."""
        if not self.metadata:
            self.metadata = {}
        if not self.id:
            self.id = str(hash(self.content))

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary.

        Returns:
            Dictionary representation of document
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "embeddings": self.embeddings,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary.

        Args:
            data: Dictionary representation of document

        Returns:
            Document instance
        """
        return cls(
            content=data["content"],
            metadata=data.get("metadata", {}),
            embeddings=data.get("embeddings"),
            id=data.get("id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
        )
