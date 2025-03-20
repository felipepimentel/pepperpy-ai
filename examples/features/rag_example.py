#!/usr/bin/env python3
"""
Example demonstrating the PepperPy RAG (Retrieval Augmented Generation) module.
"""

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Document:
    """Represents a document in the knowledge base."""

    id: str
    content: str
    metadata: Dict[str, Any]

    @classmethod
    def create(
        cls, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> "Document":
        """Create a new document with a unique ID."""
        return cls(
            id=str(uuid.uuid4()),
            content=content,
            metadata=metadata or {},
        )


class VectorStore:
    """Simple in-memory vector store for demonstration purposes."""

    def __init__(self) -> None:
        """Initialize the vector store."""
        self.documents: Dict[str, Document] = {}
        # In a real implementation, this would store embeddings
        self.vectors: Dict[str, List[float]] = {}

    async def add_document(self, document: Document) -> None:
        """Add a document to the vector store."""
        self.documents[document.id] = document
        # In a real implementation, this would compute embeddings
        # For demonstration, we'll just use a simple mock
        self.vectors[document.id] = [0.1] * 10  # Mock embedding

    async def search(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """Search for documents similar to the query."""
        # In a real implementation, this would compute query embedding
        # and perform similarity search
        # For demonstration, we'll just return random documents
        results = []
        for doc_id, doc in list(self.documents.items())[:top_k]:
            # Mock similarity score between 0.5 and 0.9
            score = 0.5 + (hash(doc_id + query) % 40) / 100
            results.append((doc, score))

        # Sort by score in descending order
        results.sort(key=lambda x: x[1], reverse=True)
        return results


class Chunker:
    """Splits documents into chunks for processing."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        """Initialize the chunker."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def split_document(self, document: Document) -> List[Document]:
        """Split a document into chunks."""
        content = document.content
        chunks = []

        # Simple character-based chunking for demonstration
        for i in range(0, len(content), self.chunk_size - self.chunk_overlap):
            chunk_content = content[i : i + self.chunk_size]
            if not chunk_content.strip():
                continue

            chunk = Document.create(
                content=chunk_content,
                metadata={
                    **document.metadata,
                    "parent_id": document.id,
                    "chunk_index": len(chunks),
                },
            )
            chunks.append(chunk)

        return chunks


class RAGPipeline:
    """Retrieval Augmented Generation pipeline."""

    def __init__(
        self,
        vector_store: VectorStore,
        chunker: Chunker,
        llm_prompt_template: str = "Answer the question based on the context:\n\nContext: {context}\n\nQuestion: {query}\n\nAnswer:",
    ) -> None:
        """Initialize the RAG pipeline."""
        self.vector_store = vector_store
        self.chunker = chunker
        self.llm_prompt_template = llm_prompt_template

    async def add_document(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Add a document to the knowledge base."""
        # Create the document
        document = Document.create(content=content, metadata=metadata)

        # Split into chunks
        chunks = await self.chunker.split_document(document)

        # Add chunks to vector store
        for chunk in chunks:
            await self.vector_store.add_document(chunk)

        return document

    async def query(self, query: str, top_k: int = 3) -> str:
        """Query the RAG pipeline."""
        # Retrieve relevant documents
        results = await self.vector_store.search(query, top_k=top_k)

        # Format context from retrieved documents
        context = "\n\n".join([
            f"[Document {i + 1} (Score: {score:.2f})]: {doc.content}"
            for i, (doc, score) in enumerate(results)
        ])

        # Generate prompt for LLM
        prompt = self.llm_prompt_template.format(context=context, query=query)

        # In a real implementation, this would call an LLM API
        # For demonstration, we'll just return a mock response
        response = await self._mock_llm_call(prompt)

        return response

    async def _mock_llm_call(self, prompt: str) -> str:
        """Mock LLM call for demonstration purposes."""
        # Simulate processing time
        await asyncio.sleep(0.5)

        # Extract the query from the prompt
        query_start = prompt.find("Question: ") + 10
        query_end = prompt.find("\n\nAnswer:")
        query = prompt[query_start:query_end]

        # Generate a simple response based on the query
        if "weather" in query.lower():
            return "Based on the provided context, the weather is expected to be sunny with a high of 75°F."
        elif "capital" in query.lower():
            return "According to the retrieved documents, the capital city is Paris, which has been the capital of France since 987 CE."
        elif "recipe" in query.lower():
            return "The context provides a recipe for chocolate chip cookies that includes flour, sugar, butter, and chocolate chips as the main ingredients."
        else:
            return "Based on the retrieved documents, I can provide the following answer: The information you're looking for appears to be related to general knowledge. The documents suggest that further research might be needed for a more specific answer."


async def main() -> None:
    """Run the RAG example."""
    print("PepperPy RAG Example")
    print("===================")

    # Initialize components
    vector_store = VectorStore()
    chunker = Chunker(chunk_size=200, chunk_overlap=50)
    rag_pipeline = RAGPipeline(vector_store, chunker)

    # Add some documents to the knowledge base
    print("\nAdding documents to the knowledge base...")

    await rag_pipeline.add_document(
        content="Paris is the capital and most populous city of France. It has been one of "
        "Europe's major centers of finance, diplomacy, commerce, fashion, and arts "
        "since the 17th century. Paris is located on the Seine River in northern France.",
        metadata={"source": "geography", "topic": "cities"},
    )

    await rag_pipeline.add_document(
        content="The weather in Paris is generally mild. Summers are warm with average high "
        "temperatures of around 25°C (77°F). Winters are cold but not freezing, with "
        "average temperatures of about 5°C (41°F). Paris receives moderate rainfall "
        "throughout the year, with slightly more precipitation in winter.",
        metadata={"source": "geography", "topic": "climate"},
    )

    await rag_pipeline.add_document(
        content="A classic chocolate chip cookie recipe includes: 2 1/4 cups all-purpose flour, "
        "1 teaspoon baking soda, 1 teaspoon salt, 1 cup butter, 3/4 cup granulated sugar, "
        "3/4 cup brown sugar, 2 eggs, 2 teaspoons vanilla extract, and 2 cups chocolate chips. "
        "Bake at 375°F for 9-11 minutes for the perfect cookies.",
        metadata={"source": "cooking", "topic": "recipes"},
    )

    # Query the RAG pipeline
    print("\nQuerying the RAG pipeline...")

    queries = [
        "What is the capital of France?",
        "How is the weather in Paris?",
        "Can you give me a recipe for cookies?",
        "What is the population of Tokyo?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        response = await rag_pipeline.query(query)
        print(f"Response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
