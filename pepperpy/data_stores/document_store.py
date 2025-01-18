"""Document storage module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pepperpy.common.types import JSON


@dataclass
class DocumentMetadata:
    """Document metadata."""

    id: str
    source: str
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]


@dataclass
class DocumentStoreConfig:
    """Document store configuration."""

    storage_path: str
    backup_enabled: bool = False
    backup_interval: int = 3600
    max_documents: int | None = None


class DocumentStore:
    """Document storage class."""

    def __init__(self, config: DocumentStoreConfig) -> None:
        """Initialize document store.

        Args:
            config: Store configuration
        """
        self.config = config
        self.documents: dict[str, JSON] = {}
        self.metadata: dict[str, DocumentMetadata] = {}

    async def setup(self) -> None:
        """Set up document store."""
        pass

    async def cleanup(self) -> None:
        """Clean up document store."""
        pass

    async def add_document(self, document: JSON, metadata: DocumentMetadata) -> None:
        """Add document to store.

        Args:
            document: Document to add
            metadata: Document metadata
        """
        self.documents[metadata.id] = document
        self.metadata[metadata.id] = metadata

    async def get_document(self, doc_id: str) -> JSON | None:
        """Get document from store.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(doc_id)

    async def get_metadata(self, doc_id: str) -> DocumentMetadata | None:
        """Get document metadata.

        Args:
            doc_id: Document ID

        Returns:
            Metadata if found, None otherwise
        """
        return self.metadata.get(doc_id)

    async def update_document(self, doc_id: str, document: JSON) -> None:
        """Update document in store.

        Args:
            doc_id: Document ID
            document: Updated document
        """
        if doc_id in self.documents:
            self.documents[doc_id] = document
            self.metadata[doc_id].updated_at = datetime.now()

    async def delete_document(self, doc_id: str) -> None:
        """Delete document from store.

        Args:
            doc_id: Document ID
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.metadata[doc_id]

    async def list_documents(self) -> list[str]:
        """List document IDs.

        Returns:
            List of document IDs
        """
        return list(self.documents.keys())
