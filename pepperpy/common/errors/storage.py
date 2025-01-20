"""Storage error handling utilities."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from . import (
    StorageError,
    VectorStoreError,
    DocumentStoreError,
    MemoryStoreError,
)


class StorageConnectionError(StorageError):
    """Error raised when connection to storage fails."""
    
    def __init__(
        self,
        message: str,
        store_type: str,
        connection_info: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            store_type: Type of storage.
            connection_info: Connection information.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.store_type = store_type
        self.connection_info = connection_info
        self.details = details or {}


class StorageOperationError(StorageError):
    """Error raised when storage operation fails."""
    
    def __init__(
        self,
        message: str,
        store_type: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            store_type: Type of storage.
            operation: Failed operation.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.store_type = store_type
        self.operation = operation
        self.details = details or {}


class VectorIndexError(VectorStoreError):
    """Error raised for vector index operations."""
    
    def __init__(
        self,
        message: str,
        index_type: str,
        dimension: int,
        metric: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            index_type: Type of vector index.
            dimension: Vector dimension.
            metric: Distance metric.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.index_type = index_type
        self.dimension = dimension
        self.metric = metric
        self.details = details or {}


class DocumentNotFoundError(DocumentStoreError):
    """Error raised when document is not found."""
    
    def __init__(
        self,
        message: str,
        document_id: str,
        store_path: Optional[Union[str, Path]] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            document_id: ID of missing document.
            store_path: Path to document store.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.document_id = document_id
        self.store_path = store_path
        self.details = details or {}


class DocumentChunkError(DocumentStoreError):
    """Error raised when document chunking fails."""
    
    def __init__(
        self,
        message: str,
        document_id: str,
        chunk_size: int,
        chunk_overlap: int,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            document_id: Document ID.
            chunk_size: Size of chunks.
            chunk_overlap: Overlap between chunks.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.document_id = document_id
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.details = details or {}


class MemoryExpiredError(MemoryStoreError):
    """Error raised when memory has expired."""
    
    def __init__(
        self,
        message: str,
        memory_id: str,
        ttl: int,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            memory_id: Memory ID.
            ttl: Time-to-live in seconds.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.memory_id = memory_id
        self.ttl = ttl
        self.details = details or {}


class MemoryCapacityError(MemoryStoreError):
    """Error raised when memory store is full."""
    
    def __init__(
        self,
        message: str,
        store_type: str,
        max_size: int,
        current_size: int,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message.
            store_type: Type of memory store.
            max_size: Maximum store size.
            current_size: Current store size.
            details: Additional error details.
            cause: Original exception that caused this error.
        """
        super().__init__(message, cause)
        self.store_type = store_type
        self.max_size = max_size
        self.current_size = current_size
        self.details = details or {} 