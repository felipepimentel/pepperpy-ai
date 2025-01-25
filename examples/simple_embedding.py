"""Example of using the embedding provider."""

import asyncio
from typing import List

from pepperpy.providers.embedding import EmbeddingConfig, EmbeddingManager
from pepperpy.providers.vector_store.base import Embeddings


async def main():
    """Run the example."""
    # Initialize embedding manager
    manager = EmbeddingManager()
    await manager.initialize({
        "primary": {
            "type": "sentence_transformers",
            "model_name": "all-MiniLM-L6-v2",
            "device": "cpu"
        }
    })
    
    try:
        # Generate embeddings
        texts = [
            "Hello, world!",
            "How are you?",
            "Nice to meet you!"
        ]
        
        embeddings: List[Embeddings] = await manager.embed_batch(texts)
        
        # Print results
        for emb in embeddings:
            print(f"Text: {emb.text}")
            print(f"Vector shape: {emb.vector.shape}")
            print(f"Vector type: {emb.vector.dtype}")
            print("---")
            
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 