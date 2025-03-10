#!/usr/bin/env python
"""Simple example of using the PepperPy RAG module.

This example demonstrates how to use the PepperPy RAG module to build a simple
Retrieval Augmented Generation system.
"""

import asyncio
import os
from typing import List

from pepperpy.core.interfaces import ProviderConfig
from pepperpy.llm import (
    Message,
    create_provider,
)
from pepperpy.rag import (
    Chunk,
    Document,
    DocumentType,
    Query,
    RAGPipeline,
)


class SimpleDocumentLoader:
    """Simple document loader that loads text from a string."""

    async def load(self, source: str) -> Document:
        """Load a document from a string.

        Args:
            source: The text content

        Returns:
            The loaded document
        """
        return Document(
            id="doc1",
            content=source,
            doc_type=DocumentType.TEXT,
            metadata={"source": "example"},
        )


class SimpleChunker:
    """Simple chunker that splits text by paragraphs."""

    async def process(self, document: Document) -> List[Chunk]:
        """Split a document into chunks.

        Args:
            document: The document to split

        Returns:
            The chunks
        """
        paragraphs = document.content.split("\n\n")
        chunks = []

        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue

            chunks.append(
                Chunk(
                    id=f"{document.id}-chunk-{i}",
                    content=paragraph,
                    doc_id=document.id,
                    metadata={"index": i},
                )
            )

        return chunks


class SimpleEmbedder:
    """Simple embedder that doesn't actually embed anything."""

    async def process(self, text: str) -> List[float]:
        """Generate a dummy embedding.

        Args:
            text: The text to embed

        Returns:
            A dummy embedding
        """
        # In a real implementation, this would call an embedding model
        return [0.1, 0.2, 0.3, 0.4, 0.5]


class SimpleVectorStore:
    """Simple vector store that stores chunks in memory."""

    def __init__(self):
        """Initialize the vector store."""
        self.chunks = []

    async def add(self, chunks: List[Chunk]) -> None:
        """Add chunks to the vector store.

        Args:
            chunks: The chunks to add
        """
        self.chunks.extend(chunks)

    async def search(
        self, query: Query, top_k: int = 5
    ) -> tuple[List[Chunk], List[float]]:
        """Search for chunks similar to a query.

        Args:
            query: The query to search for
            top_k: The number of results to return

        Returns:
            The retrieved chunks and their relevance scores
        """
        # In a real implementation, this would perform a vector search
        # Here we just return all chunks, sorted by index
        sorted_chunks = sorted(self.chunks, key=lambda x: x.metadata.get("index", 0))
        return sorted_chunks[:top_k], [1.0] * min(top_k, len(sorted_chunks))


class SimpleRetriever:
    """Simple retriever that uses a vector store."""

    def __init__(self, vector_store: SimpleVectorStore):
        """Initialize the retriever.

        Args:
            vector_store: The vector store to use
        """
        self.vector_store = vector_store

    async def retrieve(self, query: Query, top_k: int = 5) -> "RetrievalResult":
        """Retrieve relevant chunks for a query.

        Args:
            query: The query to retrieve chunks for
            top_k: The number of chunks to retrieve

        Returns:
            The retrieval result
        """
        from pepperpy.rag import RetrievalResult

        chunks, scores = await self.vector_store.search(query, top_k)
        return RetrievalResult(query=query, chunks=chunks, scores=scores)


class SimpleGenerator:
    """Simple generator that uses an LLM provider."""

    def __init__(self, provider):
        """Initialize the generator.

        Args:
            provider: The LLM provider to use
        """
        self.provider = provider

    async def generate(
        self, query: Query, retrieval_result: "RetrievalResult"
    ) -> "GenerationResult":
        """Generate content based on a query and retrieved chunks.

        Args:
            query: The query to generate content for
            retrieval_result: The retrieval result to use for generation

        Returns:
            The generation result
        """
        from pepperpy.rag import GenerationResult

        # Create context from retrieved chunks
        context = "\n\n".join(chunk.content for chunk in retrieval_result.chunks)

        # Create messages for the LLM
        messages = [
            Message(
                role="system",
                content="You are a helpful assistant. Answer the question based on the provided context.",
            ),
            Message(
                role="user", content=f"Context:\n{context}\n\nQuestion: {query.content}"
            ),
        ]

        # Generate response
        response = await self.provider.chat(messages, "gpt-3.5-turbo")

        return GenerationResult(
            query=query,
            content=response.message.content,
            metadata={"model": "gpt-3.5-turbo"},
        )


async def main():
    """Run the example."""
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    # Create provider configuration
    config = ProviderConfig(
        provider_type="openai",
        settings={
            "api_key": api_key,
        },
    )

    # Create provider
    provider = create_provider(config)

    # Validate provider
    await provider.validate()

    # Create RAG components
    document_loader = SimpleDocumentLoader()
    chunker = SimpleChunker()
    embedder = SimpleEmbedder()
    vector_store = SimpleVectorStore()
    retriever = SimpleRetriever(vector_store)
    generator = SimpleGenerator(provider)

    # Create RAG pipeline
    pipeline = RAGPipeline(
        document_loader=document_loader,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
        retriever=retriever,
        generator=generator,
    )

    # Sample document
    document_text = """
    PepperPy is a Python framework for building AI applications.
    
    It provides a unified interface for working with various AI components,
    including language models, embeddings, and vector stores.
    
    The framework is designed to be modular and extensible, allowing developers
    to easily integrate new components and customize existing ones.
    
    Key features include:
    - Support for multiple LLM providers
    - Retrieval Augmented Generation (RAG)
    - Memory management
    - Streaming capabilities
    - Security features
    """

    # Add document to the pipeline
    document = await pipeline.add_document(document_text)
    print(f"Added document with {len(document.chunks)} chunks")

    # Query the pipeline
    query_text = "What are the key features of PepperPy?"
    query = Query(id="query1", content=query_text)

    print(f"\nQuery: {query_text}")
    result = await pipeline.query(query)

    print(f"\nResponse: {result.content}")


if __name__ == "__main__":
    asyncio.run(main())
