"""Example demonstrating ChromaProvider with text embeddings."""

import asyncio
import numpy as np
from typing import List, Dict
from pepperpy.rag.providers.pinecone import ChromaProvider

def create_mock_embeddings(text: str, dimension: int = 5) -> List[float]:
    """Create mock embeddings for demonstration purposes.
    
    In a real application, you would use a proper embedding model
    like OpenAI's text-embedding-ada-002 or a local model.
    """
    # Create a deterministic but unique embedding for each text
    seed = sum(ord(c) for c in text)
    np.random.seed(seed)
    return list(np.random.normal(0, 1, dimension).astype(float))

async def main():
    # Initialize provider
    provider = ChromaProvider(collection_name="text_embeddings")
    await provider.initialize()

    # Sample documents
    documents = [
        {
            "title": "What is Vector Search?",
            "content": """Vector search is a technique that enables similarity-based 
            search using vector embeddings. It's particularly useful for searching 
            through text, images, and other unstructured data."""
        },
        {
            "title": "Understanding Embeddings",
            "content": """Embeddings are numerical representations of data in a 
            high-dimensional space. They capture semantic meaning, allowing for 
            more nuanced search beyond simple keyword matching."""
        },
        {
            "title": "Vector Databases",
            "content": """Vector databases are specialized databases designed to 
            store and query vector embeddings efficiently. They use various 
            algorithms to perform approximate nearest neighbor search."""
        }
    ]

    # Create vectors from documents
    vectors = []
    for i, doc in enumerate(documents):
        # In a real application, you would use a proper embedding model here
        embedding = create_mock_embeddings(doc["content"])
        vectors.append({
            "id": f"doc_{i}",
            "values": embedding,
            "metadata": {
                "title": doc["title"],
                "content": doc["content"]
            }
        })

    # Store vectors
    await provider.store(vectors)

    # Example queries
    queries = [
        "What are vector embeddings?",
        "How do vector databases work?",
        "What is similarity search?"
    ]

    print("\nPerforming semantic search for different queries:")
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        # Create query embedding
        query_embedding = create_mock_embeddings(query)
        
        # Search for similar documents
        results = await provider.search(
            query_vector=query_embedding,
            top_k=2
        )
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Title: {result.metadata['title']}")
            print(f"Score: {result.score}")
            print(f"Content: {result.metadata['content'][:100]}...")

    await provider.close()

if __name__ == "__main__":
    asyncio.run(main()) 