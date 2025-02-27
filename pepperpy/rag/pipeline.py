"""Standard RAG pipeline implementation."""

from typing import Dict, List, Optional

from .base import (
    Document,
    RagContext,
    RagPipeline,
    RagResponse,
    SearchQuery,
)


class StandardRagPipeline(RagPipeline):
    """Standard implementation of the RAG pipeline."""

    async def process(
        self, query: str, metadata: Optional[Dict[str, str]] = None
    ) -> RagResponse:
        """Process a query through the RAG pipeline.

        Args:
            query: The query to process
            metadata: Optional metadata to include in the context

        Returns:
            RagResponse containing generated content and context
        """
        # Create search query
        search_query = SearchQuery(
            text=query,
            metadata=metadata or {},
        )

        # Retrieve relevant chunks
        search_results = await self.retriever.retrieve(search_query)

        # Create context
        context = RagContext(
            query=query,
            results=search_results,
            metadata=metadata or {},
        )

        # Generate response with context
        response = await self.augmenter.augment(query, context)

        return response

    async def index_document(self, document: Document):
        """Index a document for future retrieval.

        Args:
            document: The document to index
        """
        # Split document into chunks
        chunks = await self.chunker.chunk_document(document)

        # Generate embeddings for chunks
        embeddings = await self.embedder.embed_chunks(chunks)

        # Add embeddings to index
        await self.indexer.index_embeddings(embeddings)

    async def batch_index_documents(self, documents: List[Document]):
        """Index multiple documents in batch.

        Args:
            documents: List of documents to index
        """
        for document in documents:
            await self.index_document(document)

    async def save_index(self, path: str):
        """Save the vector index to disk.

        Args:
            path: Path to save the index
        """
        await self.indexer.save(path)

    async def load_index(self, path: str):
        """Load the vector index from disk.

        Args:
            path: Path to load the index from
        """
        await self.indexer.load(path)
