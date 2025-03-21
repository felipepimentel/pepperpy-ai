"""Result module for RAG functionality.

This module provides result representation for RAG retrieval operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .document import Document
from .query import Query


@dataclass
class RetrievalResult:
    """Result of a RAG retrieval operation.

    This class represents the result of a retrieval operation in the RAG system,
    including the retrieved documents, their scores, and metadata.

    Args:
        query: Query that produced this result
        documents: Retrieved documents
        scores: Relevance scores for each document
        metadata: Optional result metadata
        id: Optional result ID
        created_at: Result creation timestamp
    """

    query: Query
    documents: List[Document]
    scores: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize result after creation."""
        if not self.metadata:
            self.metadata = {}
        if not self.id:
            self.id = str(hash(f"{self.query.id}-{len(self.documents)}"))
        if len(self.documents) != len(self.scores):
            raise ValueError("Number of documents must match number of scores")

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation of result
        """
        return {
            "id": self.id,
            "query": self.query.to_dict(),
            "documents": [doc.to_dict() for doc in self.documents],
            "scores": self.scores,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        """Create result from dictionary.

        Args:
            data: Dictionary representation of result

        Returns:
            RetrievalResult instance
        """
        return cls(
            query=Query.from_dict(data["query"]),
            documents=[Document.from_dict(doc) for doc in data["documents"]],
            scores=data["scores"],
            metadata=data.get("metadata", {}),
            id=data.get("id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
        )
