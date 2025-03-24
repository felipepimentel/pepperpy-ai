"""Example demonstrating persistent storage with ChromaProvider."""

import asyncio
import os
from pepperpy.rag.providers.pinecone import ChromaProvider

async def main():
    # Create a persistent storage directory
    persist_dir = "data/vector_store"
    os.makedirs(persist_dir, exist_ok=True)

    # Initialize provider with persistent storage
    provider = ChromaProvider(
        collection_name="persistent_collection",
        persist_directory=persist_dir
    )
    await provider.initialize()

    # Create some test vectors with more realistic embeddings
    vectors = [
        {
            "id": "article1",
            "values": [0.1, 0.2, 0.3, 0.4, 0.5],  # 5D vector
            "metadata": {
                "title": "Introduction to Vector Databases",
                "category": "technical",
                "author": "John Doe"
            }
        },
        {
            "id": "article2",
            "values": [0.2, 0.3, 0.4, 0.5, 0.6],
            "metadata": {
                "title": "Advanced Vector Search",
                "category": "technical",
                "author": "Jane Smith"
            }
        },
        {
            "id": "article3",
            "values": [0.8, 0.7, 0.6, 0.5, 0.4],
            "metadata": {
                "title": "Machine Learning Basics",
                "category": "educational",
                "author": "John Doe"
            }
        }
    ]

    # Store vectors
    await provider.store(vectors)

    # Demonstrate different search scenarios
    print("\n1. Basic similarity search:")
    results = await provider.search(
        query_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        top_k=2
    )
    for result in results:
        print(f"ID: {result.id}")
        print(f"Score: {result.score}")
        print(f"Title: {result.metadata['title']}\n")

    print("\n2. Search with category filter:")
    results = await provider.search(
        query_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        top_k=2,
        filter={"category": "technical"}
    )
    for result in results:
        print(f"ID: {result.id}")
        print(f"Score: {result.score}")
        print(f"Title: {result.metadata['title']}\n")

    print("\n3. Search with author filter:")
    results = await provider.search(
        query_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        top_k=2,
        filter={"author": "John Doe"}
    )
    for result in results:
        print(f"ID: {result.id}")
        print(f"Score: {result.score}")
        print(f"Title: {result.metadata['title']}\n")

    # Close the provider to ensure data is persisted
    await provider.close()

    print("\nData has been persisted to:", persist_dir)
    print("You can restart the application and the vectors will still be available.")

if __name__ == "__main__":
    asyncio.run(main()) 