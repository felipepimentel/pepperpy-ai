"""Document storage module."""

from dataclasses import dataclass
from datetime import datetime

from pepperpy.common.types import JSON


@dataclass
class DocumentMetadata:
    """Document metadata."""

    id: str
    created_at: datetime
    updated_at: datetime
    source: str | None = None
    tags: list[str] | None = None
    embedding: list[float] | None = None


@dataclass
class DocumentStoreConfig:
    """Document store configuration."""

    backup_enabled: bool = False
    backup_interval: int = 3600
    max_documents: int | None = None


class DocumentStore:
    """Document storage and management."""

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
        self.documents.clear()
        self.metadata.clear()

    async def store(
        self,
        doc_id: str,
        document: JSON,
        metadata: DocumentMetadata,
    ) -> None:
        """Store document with metadata.

        Args:
            doc_id: Document ID
            document: Document content
            metadata: Document metadata
        """
        self.documents[doc_id] = document
        self.metadata[doc_id] = metadata

    async def retrieve(
        self,
        doc_id: str,
    ) -> tuple[JSON | None, DocumentMetadata | None]:
        """Retrieve document and metadata by ID.

        Args:
            doc_id: Document ID

        Returns:
            Tuple of document content and metadata, or None if not found
        """
        document = self.documents.get(doc_id)
        metadata = self.metadata.get(doc_id)
        return document, metadata

    async def delete(self, doc_id: str) -> None:
        """Delete document and metadata by ID.

        Args:
            doc_id: Document ID
        """
        self.documents.pop(doc_id, None)
        self.metadata.pop(doc_id, None)

    async def get_document(self, doc_id: str) -> JSON | None:
        """Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(doc_id)

    async def get_metadata(self, doc_id: str) -> DocumentMetadata | None:
        """Get document metadata by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document metadata if found, None otherwise
        """
        return self.metadata.get(doc_id)
