"""Pipeline implementations for the RAG system."""

from typing import Dict, List, Optional

from .base import Augmenter, Chunker, Embedder, Indexer, RagPipeline, Retriever
from .types import Document, RagContext, RagResponse, SearchQuery


class StandardRagPipeline(RagPipeline):
    """Standard RAG pipeline implementation."""

    def __init__(
        self,
        chunker: Chunker,
        embedder: Embedder,
        indexer: Indexer,
        retriever: Retriever,
        augmenter: Augmenter,
        name: str = "standard_rag_pipeline",
        version: str = "0.1.0",
    ):
        super().__init__(name=name, version=version)
        self.chunker = chunker
        self.embedder = embedder
        self.indexer = indexer
        self.retriever = retriever
        self.augmenter = augmenter
        self._indexed_docs: Dict[str, Document] = {}

    async def process(
        self, query: str, metadata: Optional[Dict[str, str]] = None
    ) -> RagResponse:
        """Process a query through the RAG pipeline."""
        # Create search query
        search_query = SearchQuery(
            text=query,
            filters=metadata or {},
            top_k=5,  # TODO: Make configurable
            threshold=0.0,  # TODO: Make configurable
            metadata=metadata or {},
        )

        # Retrieve relevant chunks
        results = await self.retriever.retrieve(search_query)

        # Create context
        context = RagContext(
            query=query,
            results=results,
            metadata=metadata or {},
        )

        # Generate response
        response = await self.augmenter.augment(query, context)
        return response

    async def index_document(self, document: Document):
        """Index a single document."""
        # Chunk document
        chunks = await self.chunker.chunk_document(document)

        # Generate embeddings
        embeddings = await self.embedder.embed_chunks(chunks)

        # Index embeddings
        await self.indexer.index_embeddings(embeddings)

        # Store document reference
        self._indexed_docs[document.id] = document

    async def batch_index_documents(self, documents: List[Document]):
        """Index multiple documents in batch."""
        for document in documents:
            await self.index_document(document)

    async def save_index(self, path: str):
        """Save the index to disk."""
        await self.indexer.save(path)

    async def load_index(self, path: str):
        """Load the index from disk."""
        await self.indexer.load(path)

    @property
    def indexed_documents(self) -> List[Document]:
        """Get list of indexed documents."""
        return list(self._indexed_docs.values())

    @property
    def metadata(self) -> Dict[str, str]:
        """Get pipeline metadata."""
        return {
            "chunker": self.chunker.name,
            "embedder": self.embedder.name,
            "indexer": self.indexer.name,
            "retriever": self.retriever.name,
            "augmenter": self.augmenter.name,
            "num_documents": len(self._indexed_docs),
        }
