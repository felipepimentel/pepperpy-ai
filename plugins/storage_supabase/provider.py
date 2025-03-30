"""Supabase RAG provider implementation.

This module provides a RAG provider implementation using Supabase and pgvector
for efficient vector similarity search and document storage.
"""

from typing import Any, List, Optional

import supabase  # Import the module
from supabase.client import Client  # Import Client directly

from ..document import Document
from ..provider import RAGError
from ..query import Query
from ..result import RetrievalResult


class SupabaseRAGProvider:
    """RAG provider using Supabase and pgvector for vector similarity search.

    This provider leverages Supabase's pgvector integration for efficient
    vector similarity search and document storage.

    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase project API key
        table_name: Name of the table to store documents and embeddings
        **kwargs: Additional configuration options
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        table_name: str = "documents",
        **kwargs: Any,
    ) -> None:
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.table_name = table_name
        self.client: Optional[Client] = None

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates necessary tables and indexes if they don't exist.
        """
        try:
            # Initialize Supabase client
            self.client = supabase.create_client(self.supabase_url, self.supabase_key)

            # Create table with vector support if it doesn't exist
            await self._create_table_if_not_exists()

        except Exception as e:
            raise RAGError(f"Failed to initialize SupabaseRAGProvider: {str(e)}") from e

    async def _create_table_if_not_exists(self) -> None:
        """Create the documents table with vector support if it doesn't exist."""
        if not self.client:
            raise RAGError("Provider not initialized")

        try:
            # Create extension if not exists
            await self.client.rpc(
                "create_vector_extension",
                {"extension_name": "vector"},
            )

            # Create table if not exists
            query = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB,
                embedding vector(1536)
            );
            """
            await self.client.rpc("execute_sql", {"query": query})

            # Create vector index if not exists
            index_query = f"""
            CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
            ON {self.table_name} 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """
            await self.client.rpc("execute_sql", {"query": index_query})

        except Exception as e:
            raise RAGError(f"Failed to create table: {str(e)}") from e

    async def add_documents(
        self,
        documents: List[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents to the provider.

        Args:
            documents: List of documents to add
            **kwargs: Additional arguments (unused)

        Raises:
            RAGError: If adding documents fails
        """
        if not self.client:
            raise RAGError("Provider not initialized")

        try:
            for doc in documents:
                if doc.id is None:
                    continue

                if doc.embeddings is None:
                    raise RAGError(f"Document {doc.id} has no embeddings")

                # Insert document into Supabase
                await (
                    self.client.table(self.table_name)
                    .insert(
                        {
                            "id": doc.id,
                            "content": doc.content,
                            "metadata": doc.metadata,
                            "embedding": doc.embeddings,
                        }
                    )
                    .execute()
                )

        except Exception as e:
            raise RAGError(f"Failed to add documents: {str(e)}") from e

    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents matching a query.

        Args:
            query: Query to search for
            limit: Maximum number of results to return
            **kwargs: Additional arguments (unused)

        Returns:
            Search results with documents and scores

        Raises:
            RAGError: If search fails
        """
        if not self.client:
            raise RAGError("Provider not initialized")

        try:
            if query.embeddings is None:
                raise RAGError("Query has no embeddings")

            # Perform vector similarity search
            search_query = f"""
            SELECT 
                id,
                content,
                metadata,
                1 - (embedding <=> $1::vector) as similarity
            FROM {self.table_name}
            ORDER BY similarity DESC
            LIMIT $2;
            """

            result = await self.client.rpc(
                "execute_sql",
                {
                    "query": search_query,
                    "params": [query.embeddings, limit],
                },
            ).execute()

            # Convert results to documents
            docs = []
            scores = []

            for row in result.data:
                doc = Document(
                    id=row["id"],
                    content=row["content"],
                    metadata=row["metadata"],
                )
                docs.append(doc)
                scores.append(float(row["similarity"]))

            return RetrievalResult(query=query, documents=docs, scores=scores)

        except Exception as e:
            raise RAGError(f"Failed to search: {str(e)}") from e

    async def remove_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Remove documents from the provider.

        Args:
            document_ids: IDs of documents to remove
            **kwargs: Additional arguments (unused)
        """
        if not self.client:
            raise RAGError("Provider not initialized")

        try:
            # Delete documents from Supabase
            await (
                self.client.table(self.table_name)
                .delete()
                .in_("id", document_ids)
                .execute()
            )

        except Exception as e:
            raise RAGError(f"Failed to remove documents: {str(e)}") from e

    async def get_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: ID of document to get
            **kwargs: Additional arguments (unused)

        Returns:
            Document if found, None otherwise
        """
        if not self.client:
            raise RAGError("Provider not initialized")

        try:
            result = (
                await self.client.table(self.table_name)
                .select("*")
                .eq("id", document_id)
                .execute()
            )

            if not result.data:
                return None

            row = result.data[0]
            return Document(
                id=row["id"],
                content=row["content"],
                metadata=row["metadata"],
                embeddings=row["embedding"],
            )

        except Exception as e:
            raise RAGError(f"Failed to get document: {str(e)}") from e

    async def shutdown(self) -> None:
        """Shut down the provider."""
        # No specific cleanup needed for Supabase
        pass
