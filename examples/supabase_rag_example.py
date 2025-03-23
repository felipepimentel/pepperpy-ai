"""Example of using PepperPy with Supabase RAG provider."""

import asyncio
import os

from pepperpy.rag import Document, HashEmbeddingFunction, Query
from pepperpy.rag.providers.supabase import SupabaseRAGProvider


async def main() -> None:
    """Run the example."""
    # Initialize the provider
    provider = SupabaseRAGProvider(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_KEY"],
        table_name="documents",
    )

    # Initialize embedding function
    embedding_function = HashEmbeddingFunction()

    # Initialize the provider
    await provider.initialize()

    # Create some test documents
    documents = [
        Document(
            id="doc1",
            content="Supabase is a great open source alternative to Firebase",
            metadata={"source": "example"},
        ),
        Document(
            id="doc2",
            content="PostgreSQL is a powerful open source database",
            metadata={"source": "example"},
        ),
        Document(
            id="doc3",
            content="Vector similarity search is efficient with pgvector",
            metadata={"source": "example"},
        ),
    ]

    # Add embeddings to documents
    for doc in documents:
        doc.embeddings = await embedding_function.embed_text(doc.content)

    # Add documents to the provider
    print("Adding documents...")
    await provider.add_documents(documents)

    # Create a search query
    query_text = "What is Supabase?"
    print(f"\nSearching for: {query_text}")

    query = Query(
        id="q1",
        text=query_text,
        embeddings=await embedding_function.embed_text(query_text),
    )

    # Search for documents
    results = await provider.search(query)

    # Print results
    print("\nResults:")
    for doc, score in zip(results.documents, results.scores):
        print(f"Document: {doc.content}")
        print(f"Score: {score:.4f}\n")

    # Clean up
    print("Cleaning up...")
    await provider.remove_documents([doc.id for doc in documents])
    await provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
