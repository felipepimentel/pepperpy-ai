"""Document module for managing text documents.

This module provides functionality for managing text documents,
including chunking, metadata, and storage.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pepperpy.core.utils.errors import PepperpyError


class DocumentError(PepperpyError):
    """Document error."""
    pass


@dataclass
class Document:
    """Document class for managing text content.
    
    This class represents a text document with metadata and chunking
    capabilities.
    """
    
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    chunks: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate document after initialization."""
        if not self.content:
            raise DocumentError("Document content cannot be empty")
        if not isinstance(self.metadata, dict):
            raise DocumentError("Metadata must be a dictionary")
        if not isinstance(self.chunks, list):
            raise DocumentError("Chunks must be a list")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary.
        
        Returns:
            Dictionary representation of document
        """
        return {
            "id": str(self.id),
            "content": self.content,
            "metadata": self.metadata,
            "chunks": self.chunks,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary.
        
        Args:
            data: Dictionary representation of document
            
        Returns:
            Document instance
            
        Raises:
            DocumentError: If data is invalid
        """
        if not isinstance(data, dict):
            raise DocumentError("Data must be a dictionary")
        
        required_fields = {"id", "content"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise DocumentError(f"Missing required fields: {missing_fields}")
        
        return cls(
            content=data["content"],
            metadata=data.get("metadata", {}),
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            chunks=data.get("chunks", []),
        )


class DocumentStore:
    """Document store for managing multiple documents.
    
    This class provides functionality for storing and retrieving
    documents, with support for metadata-based filtering.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize document store.
        
        Args:
            config: Optional configuration dictionary
        """
        self._config = config or {}
        self._documents: Dict[UUID, Document] = {}
        self._is_initialized = False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get store configuration."""
        return self._config
    
    @property
    def is_initialized(self) -> bool:
        """Check if store is initialized."""
        return self._is_initialized
    
    def validate(self) -> None:
        """Validate document store configuration."""
        if not isinstance(self._config, dict):
            raise DocumentError("Configuration must be a dictionary")
        if not isinstance(self._documents, dict):
            raise DocumentError("Documents must be a dictionary")
    
    def initialize(self) -> None:
        """Initialize store."""
        if self.is_initialized:
            return
        self.validate()
        self._is_initialized = True
    
    def cleanup(self) -> None:
        """Clean up store."""
        if not self.is_initialized:
            return
        self._documents.clear()
        self._is_initialized = False
    
    def add_document(self, document: Document) -> None:
        """Add document to store.
        
        Args:
            document: Document to add
            
        Raises:
            DocumentError: If adding fails
        """
        if not self.is_initialized:
            raise DocumentError("Store not initialized")
        
        if document.id in self._documents:
            raise DocumentError(f"Document already exists: {document.id}")
        
        self._documents[document.id] = document
    
    def get_document(self, id: UUID) -> Document:
        """Get document by ID.
        
        Args:
            id: Document ID
            
        Returns:
            Document instance
            
        Raises:
            DocumentError: If document not found
        """
        if not self.is_initialized:
            raise DocumentError("Store not initialized")
        
        if id not in self._documents:
            raise DocumentError(f"Document not found: {id}")
        
        return self._documents[id]
    
    def list_documents(self) -> List[Document]:
        """List all documents.
        
        Returns:
            List of documents
            
        Raises:
            DocumentError: If listing fails
        """
        if not self.is_initialized:
            raise DocumentError("Store not initialized")
        
        return list(self._documents.values())
    
    def remove_document(self, id: UUID) -> None:
        """Remove document.
        
        Args:
            id: Document ID
            
        Raises:
            DocumentError: If removal fails
        """
        if not self.is_initialized:
            raise DocumentError("Store not initialized")
        
        if id not in self._documents:
            raise DocumentError(f"Document not found: {id}")
        
        del self._documents[id]
    
    def clear(self) -> None:
        """Clear all documents.
        
        Raises:
            DocumentError: If clearing fails
        """
        if not self.is_initialized:
            raise DocumentError("Store not initialized")
        
        self._documents.clear()
    
    def filter_by_metadata(
        self,
        filters: Dict[str, Any]
    ) -> List[Document]:
        """Filter documents by metadata.
        
        Args:
            filters: Metadata filters
            
        Returns:
            List of matching documents
            
        Raises:
            DocumentError: If filtering fails
        """
        if not self.is_initialized:
            raise DocumentError("Store not initialized")
        
        if not isinstance(filters, dict):
            raise DocumentError("Filters must be a dictionary")
        
        filtered = []
        for doc in self._documents.values():
            matches = True
            for key, value in filters.items():
                if key not in doc.metadata or doc.metadata[key] != value:
                    matches = False
                    break
            if matches:
                filtered.append(doc)
        
        return filtered 