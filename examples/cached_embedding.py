"""Example of using cached embeddings.

This example demonstrates how to use the CachedEmbedder class to efficiently
generate and cache embeddings for text data.
"""

import asyncio
from typing import List

import numpy as np

from pepperpy.interfaces.embeddings import CachedEmbedder, TextEmbedder
from pepperpy.caching.vector import VectorCache


async def main():
    """Run the cached embedding example."""
    # Create a text embedder
    embedder = TextEmbedder(model_name="all-MiniLM-L6-v2")
    await embedder.initialize()
    
    # Create a vector cache
    cache = VectorCache(max_size=1000)
    
    # Create a cached embedder
    cached_embedder = CachedEmbedder(embedder=embedder, cache=cache)
    
    # Example texts
    texts = [
        "This is an example sentence for embedding.",
        "Another example sentence to demonstrate caching.",
        "The cached embedder will store these vectors.",
        "This is an example sentence for embedding.",  # Duplicate to demonstrate cache hit
    ]
    
    # First run - should compute all embeddings
    print("First run - computing embeddings:")
    start_time = asyncio.get_event_loop().time()
    embeddings = await cached_embedder.embed(texts)
    end_time = asyncio.get_event_loop().time()
    print(f"Generated {len(embeddings)} embeddings in {end_time - start_time:.4f} seconds")
    print(f"Embedding shape: {embeddings.shape}")
    
    # Second run - should use cache for all embeddings
    print("\nSecond run - using cached embeddings:")
    start_time = asyncio.get_event_loop().time()
    embeddings = await cached_embedder.embed(texts)
    end_time = asyncio.get_event_loop().time()
    print(f"Retrieved {len(embeddings)} embeddings in {end_time - start_time:.4f} seconds")
    
    # Add a new text
    texts.append("This is a new sentence that wasn't cached before.")
    
    # Third run - should use cache for existing embeddings and compute only the new one
    print("\nThird run - mixed cache hits and misses:")
    start_time = asyncio.get_event_loop().time()
    embeddings = await cached_embedder.embed(texts)
    end_time = asyncio.get_event_loop().time()
    print(f"Retrieved/generated {len(embeddings)} embeddings in {end_time - start_time:.4f} seconds")
    
    # Clean up
    await embedder.cleanup()


if __name__ == "__main__":
    asyncio.run(main())