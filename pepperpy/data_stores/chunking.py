"""Chunking module for data stores."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class Chunk:
    """Represents a chunk of data with metadata."""
    
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        """Validate chunk after initialization."""
        if not self.text:
            raise ValueError("Chunk text cannot be empty")
        
        if not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")
        
        if self.embedding is not None and not isinstance(self.embedding, list):
            raise ValueError("Embedding must be a list of floats")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary.
        
        Returns:
            Dictionary representation of chunk
        """
        return {
            "id": str(self.id),
            "text": self.text,
            "metadata": self.metadata,
            "embedding": self.embedding,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """Create chunk from dictionary.
        
        Args:
            data: Dictionary representation of chunk
            
        Returns:
            Chunk instance
            
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        required_fields = {"id", "text"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return cls(
            text=data["text"],
            metadata=data.get("metadata", {}),
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            embedding=data.get("embedding"),
        )
    
    def __len__(self) -> int:
        """Get length of chunk text."""
        return len(self.text)
    
    def __str__(self) -> str:
        """Get string representation of chunk."""
        return f"Chunk(id={self.id}, text={self.text[:50]}...)"
    
    def __repr__(self) -> str:
        """Get detailed string representation of chunk."""
        return (
            f"Chunk(id={self.id}, "
            f"text={self.text[:50]}..., "
            f"metadata={self.metadata}, "
            f"embedding={self.embedding[:5] if self.embedding else None}...)"
        ) 