"""Integration between memory and data stores."""

from typing import Any, cast

from pepperpy.data_stores.document_store import DocumentStore
from pepperpy.data_stores.embedding_manager import EmbeddingManager
from pepperpy.data_stores.vector_db import BaseVectorDB, Document, SearchResult


class MemoryIntegration:
    """Integrates memory management with data stores.

    This class provides:
    - Unified interface for memory operations
    - Automatic synchronization between stores
    - Efficient retrieval strategies
    - Memory cleanup and optimization
    """

    def __init__(
        self,
        vector_db: BaseVectorDB,
        document_store: DocumentStore,
        embedding_manager: EmbeddingManager,
    ) -> None:
        """Initialize memory integration.

        Args:
            vector_db: Vector database for semantic search
            document_store: Document store for content
            embedding_manager: Embedding manager for vectors
        """
        self.vector_db = vector_db
        self.document_store = document_store
        self.embedding_manager = embedding_manager

    async def add_to_memory(
        self, texts: str | list[str], metadata: dict[str, Any] | None = None
    ) -> str | list[str]:
        """Add text(s) to memory.

        Args:
            texts: Text or list of texts to add
            metadata: Optional metadata for the texts

        Returns:
            Document ID(s)

        Raises:
            Exception: If addition fails
        """
        # Convert to list
        single_text = isinstance(texts, str)
        texts_list = [texts] if single_text else texts
        metadata_list = [metadata or {}] * len(texts_list)

        # Generate embeddings
        embeddings = await self.embedding_manager.get_embeddings(texts_list)
        embeddings_list = cast(list[list[float]], embeddings)

        # Create documents
        documents = [
            Document(
                id=f"mem_{i}",  # TODO: Better ID generation
                text=text,
                metadata=meta,
                embedding=emb,
            )
            for i, (text, meta, emb) in enumerate(
                zip(texts_list, metadata_list, embeddings_list, strict=False)
            )
        ]

        # Store in both databases
        doc_ids = await self.document_store.store(documents)
        await self.vector_db.add_documents(documents)

        return doc_ids[0] if single_text else doc_ids

    async def search_memory(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
        full_documents: bool = True,
    ) -> list[SearchResult | Document]:
        """Search memory for relevant content.

        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            full_documents: Whether to return full documents

        Returns:
            Search results or documents

        Raises:
            Exception: If search fails
        """
        # Get query embedding
        query_embedding = await self.embedding_manager.get_embeddings(query)
        query_embedding_list = cast(list[float], query_embedding)

        # Search vector database
        results = await self.vector_db.search(
            query_embedding=query_embedding_list, k=k, filter=filter
        )

        if not full_documents:
            return results

        # Get full documents
        doc_ids = [result.document.id for result in results]
        documents = await self.document_store.retrieve(doc_ids)
        if documents is None:
            return []

        # Add similarity scores
        for doc, result in zip(documents, results, strict=False):
            if doc:
                doc.metadata["similarity_score"] = result.score

        return [doc for doc in documents if doc is not None]

    async def forget(self, document_ids: str | list[str]) -> None:
        """Remove content from memory.

        Args:
            document_ids: ID(s) to remove

        Raises:
            Exception: If removal fails
        """
        # Delete from both stores
        await self.document_store.delete(document_ids)
        await self.vector_db.delete(document_ids)

    async def merge_memories(
        self, source_ids: list[str], strategy: str = "concatenate"
    ) -> str:
        """Merge multiple memories into one.

        Args:
            source_ids: IDs of memories to merge
            strategy: Merging strategy ("concatenate" or "summarize")

        Returns:
            ID of the merged memory

        Raises:
            Exception: If merging fails
        """
        # Get source documents
        documents = await self.document_store.retrieve(source_ids)
        if documents is None:
            raise ValueError("No valid documents to merge")

        documents = [doc for doc in documents if doc is not None]

        if not documents:
            raise ValueError("No valid documents to merge")

        # Merge based on strategy
        if strategy == "concatenate":
            merged_text = "\n\n".join(doc.text for doc in documents)
        elif strategy == "summarize":
            # TODO: Implement summarization
            raise NotImplementedError("Summarization not implemented yet")
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        # Create merged document
        merged_id = await self.add_to_memory(
            merged_text, metadata={"source_ids": source_ids, "merge_strategy": strategy}
        )

        # Cast to str since we know we're adding a single document
        return cast(str, merged_id)

    async def optimize_memory(
        self, max_size: int | None = None, min_relevance: float | None = None
    ) -> None:
        """Optimize memory by removing or consolidating content.

        Args:
            max_size: Optional maximum number of documents to keep
            min_relevance: Optional minimum relevance score to keep

        Raises:
            Exception: If optimization fails
        """
        try:
            # Get all documents with their relevance scores
            # Empty query for general relevance
            query_embedding = await self.embedding_manager.get_embeddings("")
            query_embedding_list = cast(list[float], query_embedding)

            results = await self.vector_db.search(
                query_embedding=query_embedding_list,
                k=max_size or 1000000,  # Large number if no max_size
            )

            # Sort by relevance score
            sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

            # Filter by minimum relevance if specified
            if min_relevance is not None:
                sorted_results = [r for r in sorted_results if r.score >= min_relevance]

            # Trim to max size if specified
            if max_size is not None and len(sorted_results) > max_size:
                to_remove = sorted_results[max_size:]
                # Remove excess documents
                for result in to_remove:
                    await self.forget(result.document.id)

            # Attempt to consolidate similar documents
            if len(sorted_results) > 1:
                clusters = self._cluster_similar_documents(sorted_results)
                for cluster in clusters:
                    if len(cluster) > 1:
                        # Merge documents in each cluster
                        await self.merge_memories(
                            source_ids=[doc.id for doc in cluster],
                            strategy="concatenate",
                        )

        except Exception as e:
            raise Exception(f"Memory optimization failed: {e!s}") from e

    def _cluster_similar_documents(
        self, results: list[SearchResult], similarity_threshold: float = 0.8
    ) -> list[list[Document]]:
        """Cluster similar documents together.

        Args:
            results: Search results to cluster
            similarity_threshold: Minimum similarity score to group documents

        Returns:
            List of document clusters
        """
        # TODO: Implement clustering logic
        return [[doc.document for doc in results]]

    async def cleanup(self) -> None:
        """Clean up resources used by memory integration.

        This includes:
        - Cleaning up vector database resources
        - Saving document store state
        - Freeing embedding manager resources
        """
        await self.vector_db.cleanup()
        await self.document_store.cleanup()
        await self.embedding_manager.cleanup()
