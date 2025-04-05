"""
PepperPy RAG Results.

Result classes for retrieval-augmented generation operations.
"""

from typing import Any

from pepperpy.core.results import TextResult


class RetrievalResult(TextResult):
    """Result of a document retrieval operation."""

    def __init__(
        self,
        content: str,
        documents: list[dict[str, Any]],
        query: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize retrieval result.

        Args:
            content: Generated content
            documents: Retrieved documents
            query: Original query
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.documents = documents
        self.query = query

        # Add to metadata
        self.metadata["document_count"] = len(documents)
        self.metadata["query"] = query

    @property
    def document_count(self) -> int:
        """Get the number of retrieved documents.

        Returns:
            Document count
        """
        return len(self.documents)

    def get_document(self, index: int) -> dict[str, Any] | None:
        """Get document at specific index.

        Args:
            index: Document index

        Returns:
            Document dictionary or None if out of range
        """
        if 0 <= index < len(self.documents):
            return self.documents[index]
        return None


class RAGResult(RetrievalResult):
    """Result of a retrieval-augmented generation operation."""

    def __init__(
        self,
        content: str,
        documents: list[dict[str, Any]],
        query: str,
        model: str,
        prompt: str,
        usage: dict[str, int],
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize RAG result.

        Args:
            content: Generated content
            documents: Retrieved documents
            query: Original query
            model: Model used
            prompt: Prompt used (with context)
            usage: Token usage information
            metadata: Additional metadata
        """
        super().__init__(
            content=content,
            documents=documents,
            query=query,
            metadata=metadata or {},
        )
        self.model = model
        self.prompt = prompt
        self.usage = usage

        # Add to metadata
        self.metadata["model"] = model
        self.metadata["usage"] = usage

    @property
    def total_tokens(self) -> int:
        """Get total tokens used.

        Returns:
            Total token count
        """
        return self.usage.get("total_tokens", 0)


class ChunkResult(TextResult):
    """Result of a document chunking operation."""

    def __init__(
        self,
        content: str,
        chunks: list[dict[str, Any]],
        source: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize chunk result.

        Args:
            content: Summary content
            chunks: Document chunks
            source: Source document
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.chunks = chunks
        self.source = source

        # Add to metadata
        self.metadata["chunk_count"] = len(chunks)
        self.metadata["source"] = source

    @property
    def chunk_count(self) -> int:
        """Get the number of chunks.

        Returns:
            Chunk count
        """
        return len(self.chunks)


class IndexResult(TextResult):
    """Result of a document indexing operation."""

    def __init__(
        self,
        content: str,
        index_name: str,
        document_count: int,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize index result.

        Args:
            content: Operation content/summary
            index_name: Name of the index
            document_count: Number of documents indexed
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.index_name = index_name
        self.document_count = document_count

        # Add to metadata
        self.metadata["index_name"] = index_name
        self.metadata["document_count"] = document_count
