"""Base document store classes for Pepperpy."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import StorageError
from ...core.lifecycle import Lifecycle

T = TypeVar("T")

class Document(PepperpyObject, DictInitializable, Validatable):
    """Base class for documents."""
    
    def __init__(
        self,
        id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize document.
        
        Args:
            id: Document ID
            content: Document content
            metadata: Optional document metadata
        """
        self._id = id
        self._content = content
        self._metadata = metadata or {}
        
    @property
    def id(self) -> str:
        """Return document ID."""
        return self._id
        
    @property
    def content(self) -> str:
        """Return document content."""
        return self._content
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return document metadata."""
        return self._metadata
        
    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(id={self.id}, content={self.content[:50]}...)"
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary.
        
        Args:
            data: Dictionary with document data
            
        Returns:
            Document instance
        """
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata"),
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary.
        
        Returns:
            Dictionary with document data
        """
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
        }
        
    def validate(self) -> None:
        """Validate document state."""
        if not self.id:
            raise ValueError("Document ID cannot be empty")
            
        if not self.content:
            raise ValueError("Document content cannot be empty")
            
class DocumentStore(Lifecycle, ABC):
    """Base class for document stores."""
    
    def __init__(
        self,
        name: str,
        store_path: Optional[str] = None,
    ) -> None:
        """Initialize document store.
        
        Args:
            name: Store name
            store_path: Optional path to store documents
        """
        super().__init__(name)
        self._store_path = store_path
        
    @property
    def store_path(self) -> Optional[str]:
        """Return store path."""
        return self._store_path
        
    async def add(self, documents: List[Document]) -> None:
        """Add documents to store.
        
        Args:
            documents: Documents to add
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Document store not initialized")
            
        await self._add(documents)
        
    @abstractmethod
    async def _add(self, documents: List[Document]) -> None:
        """Add documents implementation."""
        pass
        
    async def get(self, id: str) -> Optional[Document]:
        """Get document by ID.
        
        Args:
            id: Document ID
            
        Returns:
            Document if found, None otherwise
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Document store not initialized")
            
        return await self._get(id)
        
    @abstractmethod
    async def _get(self, id: str) -> Optional[Document]:
        """Get document implementation."""
        pass
        
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for documents.
        
        Args:
            query: Search query
            limit: Maximum number of results (default: 10)
            filters: Optional metadata filters
            
        Returns:
            List of matching documents
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Document store not initialized")
            
        return await self._search(query, limit, filters)
        
    @abstractmethod
    async def _search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search implementation."""
        pass
        
    async def delete(self, ids: List[str]) -> None:
        """Delete documents from store.
        
        Args:
            ids: Document IDs to delete
            
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Document store not initialized")
            
        await self._delete(ids)
        
    @abstractmethod
    async def _delete(self, ids: List[str]) -> None:
        """Delete implementation."""
        pass
        
    async def clear(self) -> None:
        """Clear all documents from store.
        
        Raises:
            StorageError: If store is not initialized
        """
        if not self._initialized:
            raise StorageError("Document store not initialized")
            
        await self._clear()
        
    @abstractmethod
    async def _clear(self) -> None:
        """Clear implementation."""
        pass
        
    def validate(self) -> None:
        """Validate store state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Store name cannot be empty") 