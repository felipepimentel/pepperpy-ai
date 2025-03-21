"""Query module for RAG functionality.

This module provides query representation and processing for RAG.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Query:
    """Query representation for RAG.

    This class represents a query in the RAG system, including its text,
    metadata, and embeddings.

    Args:
        text: Query text
        metadata: Optional query metadata
        embeddings: Optional query embeddings
        id: Optional query ID
        created_at: Query creation timestamp
    """

    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize query after creation."""
        if not self.metadata:
            self.metadata = {}
        if not self.id:
            self.id = str(hash(self.text))

    def to_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary.

        Returns:
            Dictionary representation of query
        """
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
            "embeddings": self.embeddings,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Query":
        """Create query from dictionary.

        Args:
            data: Dictionary representation of query

        Returns:
            Query instance
        """
        return cls(
            text=data["text"],
            metadata=data.get("metadata", {}),
            embeddings=data.get("embeddings"),
            id=data.get("id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
        )
