"""Core functionality for RAG.

This module provides the core functionality for Retrieval-Augmented Generation (RAG),
including document processing, vector storage, and query processing.
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.llm.core import LLMManager, get_llm_manager
from pepperpy.rag.document.core import (
    Document,
    DocumentChunk,
    DocumentProcessor,
    DocumentStore,
)
from pepperpy.rag.errors import (
    DocumentError,
    PipelineError,
    RAGError,
)
from pepperpy.rag.pipeline.core import (
    PipelineManager,
    Query,
    QueryResult,
    get_pipeline_manager,
)
from pepperpy.rag.storage.core import (
    ScoredChunk,
    VectorEmbedding,
    VectorStoreManager,
    get_vector_store_manager,
)
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class RAGManager:
    """Manager for RAG.

    The RAG manager provides a unified interface for working with RAG components,
    including document processing, vector storage, and query processing.
    """

    def __init__(
        self,
        document_store: Optional[DocumentStore] = None,
        document_processor: Optional[DocumentProcessor] = None,
        llm_manager: Optional[LLMManager] = None,
        vector_store_manager: Optional[VectorStoreManager] = None,
        pipeline_manager: Optional[PipelineManager] = None,
    ):
        """Initialize the RAG manager.

        Args:
            document_store: The document store to use, or None to use a memory store
            document_processor: The document processor to use, or None to use a default processor
            llm_manager: The LLM manager to use, or None to use the global manager
            vector_store_manager: The vector store manager to use, or None to use the global manager
            pipeline_manager: The pipeline manager to use, or None to use the global manager
        """
        self.document_store = document_store
        self.document_processor = document_processor
        self.llm_manager = llm_manager or get_llm_manager()
        self.vector_store_manager = vector_store_manager or get_vector_store_manager()
        self.pipeline_manager = pipeline_manager or get_pipeline_manager()

    async def add_document(
        self,
        document: Union[str, Document],
        store_document: bool = True,
        process_document: bool = True,
        embed_chunks: bool = True,
        vector_store: Optional[str] = None,
    ) -> Document:
        """Add a document to the RAG system.

        Args:
            document: The document to add, or a string containing the document content
            store_document: Whether to store the document in the document store
            process_document: Whether to process the document into chunks
            embed_chunks: Whether to embed the document chunks
            vector_store: The name of the vector store to use, or None to use the default

        Returns:
            The added document

        Raises:
            RAGError: If there is an error adding the document
        """
        # Check if we have a document store
        if store_document and self.document_store is None:
            raise RAGError("No document store is available")

        # Check if we have a document processor
        if process_document and self.document_processor is None:
            raise RAGError("No document processor is available")

        # Convert the document to a Document object if it's a string
        if isinstance(document, str):
            document = Document(content=document)

        try:
            # Store the document
            if store_document and self.document_store is not None:
                await self.document_store.add_document(document)

            # Process the document
            if process_document and self.document_processor is not None:
                chunks = await self.document_processor.process(document)

                # Store the chunks
                if store_document and self.document_store is not None:
                    await self.document_store.add_chunks(chunks)

                # Embed the chunks
                if embed_chunks:
                    await self.embed_chunks(chunks, vector_store)

            return document
        except DocumentError as e:
            # Re-raise document errors
            raise RAGError(f"Error adding document: {e}")
        except Exception as e:
            # Wrap other errors
            raise RAGError(f"Error adding document: {e}")

    async def embed_chunks(
        self,
        chunks: List[DocumentChunk],
        vector_store: Optional[str] = None,
        llm_provider: Optional[str] = None,
    ) -> List[VectorEmbedding]:
        """Embed document chunks.

        Args:
            chunks: The document chunks to embed
            vector_store: The name of the vector store to use, or None to use the default
            llm_provider: The name of the LLM provider to use, or None to use the default

        Returns:
            The vector embeddings

        Raises:
            RAGError: If there is an error embedding the chunks
        """
        try:
            # Get the vector store
            store = self.vector_store_manager.get_store(vector_store)

            # Embed each chunk
            embeddings = []

            for chunk in chunks:
                # Generate the embedding
                vector = await self.llm_manager.embed(chunk.content, llm_provider)

                # Create the embedding
                embedding = VectorEmbedding(
                    vector=vector,
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    metadata={
                        "content": chunk.content,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        **chunk.metadata.to_dict(),
                    },
                )

                # Add the embedding to the vector store
                await store.add_embedding(embedding)

                # Add the embedding to the list
                embeddings.append(embedding)

            return embeddings
        except Exception as e:
            # Wrap errors
            raise RAGError(f"Error embedding chunks: {e}")

    async def query(
        self,
        query: Union[str, Query],
        pipeline: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """Query the RAG system.

        Args:
            query: The query to run
            pipeline: The name of the pipeline to use, or None to use the default
            context: The initial context, or None to use an empty context

        Returns:
            The query result

        Raises:
            RAGError: If there is an error querying the system
        """
        try:
            # Run the pipeline
            return await self.pipeline_manager.run(query, pipeline, context)
        except PipelineError as e:
            # Re-raise pipeline errors
            raise RAGError(f"Error querying RAG system: {e}")
        except Exception as e:
            # Wrap other errors
            raise RAGError(f"Error querying RAG system: {e}")

    async def search(
        self,
        query: Union[str, Query],
        limit: int = 10,
        min_score: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
        vector_store: Optional[str] = None,
        llm_provider: Optional[str] = None,
    ) -> List[ScoredChunk]:
        """Search for document chunks.

        Args:
            query: The query to search for
            limit: The maximum number of results to return
            min_score: The minimum similarity score
            filter_metadata: Metadata to filter the results by
            vector_store: The name of the vector store to use, or None to use the default
            llm_provider: The name of the LLM provider to use, or None to use the default

        Returns:
            The search results

        Raises:
            RAGError: If there is an error searching for chunks
        """
        try:
            # Convert the query to a Query object if it's a string
            if isinstance(query, str):
                query = Query(text=query)

            # Get the vector store
            store = self.vector_store_manager.get_store(vector_store)

            # Generate the query embedding
            query_vector = await self.llm_manager.embed(query.text, llm_provider)

            # Search for similar embeddings
            results = await store.search(
                query_vector=query_vector,
                limit=limit,
                min_score=min_score,
                filter_metadata=filter_metadata,
            )

            # Convert the results to ScoredChunk objects
            scored_chunks = []

            for embedding, score in results:
                # Get the chunk content from the embedding metadata
                content = embedding.metadata.get("content", "")

                # Create a metadata object
                metadata_dict = {
                    k: v for k, v in embedding.metadata.items() if k != "content"
                }

                # Create a document chunk
                chunk = DocumentChunk(
                    content=content,
                    metadata=metadata_dict,
                    document_id=embedding.document_id,
                    chunk_index=embedding.metadata.get("chunk_index", 0),
                    id=embedding.chunk_id,
                )

                # Create a scored chunk
                scored_chunk = ScoredChunk(chunk=chunk, score=score)

                # Add the scored chunk to the list
                scored_chunks.append(scored_chunk)

            return scored_chunks
        except Exception as e:
            # Wrap errors
            raise RAGError(f"Error searching for chunks: {e}")


# Global RAG manager
_rag_manager = RAGManager()


def get_rag_manager() -> RAGManager:
    """Get the global RAG manager.

    Returns:
        The global RAG manager
    """
    return _rag_manager


async def add_document(
    document: Union[str, Document],
    store_document: bool = True,
    process_document: bool = True,
    embed_chunks: bool = True,
    vector_store: Optional[str] = None,
) -> Document:
    """Add a document to the RAG system.

    Args:
        document: The document to add, or a string containing the document content
        store_document: Whether to store the document in the document store
        process_document: Whether to process the document into chunks
        embed_chunks: Whether to embed the document chunks
        vector_store: The name of the vector store to use, or None to use the default

    Returns:
        The added document

    Raises:
        RAGError: If there is an error adding the document
    """
    return await get_rag_manager().add_document(
        document, store_document, process_document, embed_chunks, vector_store
    )


async def query(
    query: Union[str, Query],
    pipeline: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> QueryResult:
    """Query the RAG system.

    Args:
        query: The query to run
        pipeline: The name of the pipeline to use, or None to use the default
        context: The initial context, or None to use an empty context

    Returns:
        The query result

    Raises:
        RAGError: If there is an error querying the system
    """
    return await get_rag_manager().query(query, pipeline, context)


async def search(
    query: Union[str, Query],
    limit: int = 10,
    min_score: float = 0.0,
    filter_metadata: Optional[Dict[str, Any]] = None,
    vector_store: Optional[str] = None,
    llm_provider: Optional[str] = None,
) -> List[ScoredChunk]:
    """Search for document chunks.

    Args:
        query: The query to search for
        limit: The maximum number of results to return
        min_score: The minimum similarity score
        filter_metadata: Metadata to filter the results by
        vector_store: The name of the vector store to use, or None to use the default
        llm_provider: The name of the LLM provider to use, or None to use the default

    Returns:
        The search results

    Raises:
        RAGError: If there is an error searching for chunks
    """
    return await get_rag_manager().search(
        query, limit, min_score, filter_metadata, vector_store, llm_provider
    )
