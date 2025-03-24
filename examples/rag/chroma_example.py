"""Example demonstrating basic usage of ChromaProvider."""

import asyncio
from pepperpy.rag.providers.chroma import ChromaProvider

async def main():
    # Initialize provider with in-memory storage
    provider = ChromaProvider(collection_name="test_collection")
    await provider.initialize()

    # Create some test vectors
    vectors = [
        {
            "id": "doc1",
            "values": [1.0, 0.0, 0.0],
            "metadata": {"text": "This is document 1", "category": "test"}
        },
        {
            "id": "doc2",
            "values": [0.0, 1.0, 0.0],
            "metadata": {"text": "This is document 2", "category": "test"}
        },
        {
            "id": "doc3",
            "values": [0.0, 0.0, 1.0],
            "metadata": {"text": "This is document 3", "category": "production"}
        }
    ]

    # Store vectors
    await provider.store(vectors)

    # Search for similar vectors
    query = [1.0, 0.1, 0.1]  # More similar to doc1
    results = await provider.search(query_vector=query, top_k=2)

    print("\nSearch results:")
    for result in results:
        print(f"ID: {result.id}")
        print(f"Score: {result.score}")
        print(f"Metadata: {result.metadata}\n")

    # Search with filter
    filtered_results = await provider.search(
        query_vector=query,
        top_k=2,
        filter={"category": "test"}
    )

    print("\nFiltered search results (category=test):")
    for result in filtered_results:
        print(f"ID: {result.id}")
        print(f"Score: {result.score}")
        print(f"Metadata: {result.metadata}\n")

    await provider.close()

if __name__ == "__main__":
    asyncio.run(main()) 