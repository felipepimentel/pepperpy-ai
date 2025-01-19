"""Simple example demonstrating embedding generation and vector storage."""

import asyncio
import os
from typing import Any, cast

from pepperpy.data_stores.embedding_manager import EmbeddingConfig, EmbeddingManager
from pepperpy.llms.huggingface import HuggingFaceLLM, LLMConfig


async def main() -> None:
    """Run the example."""
    # Initialize LLM with configuration from environment
    llm_config = LLMConfig(
        model_name=os.getenv("PEPPERPY_MODEL", "google/gemini-2.0-flash-exp:free"),
        model_kwargs={
            "api_key": os.getenv("PEPPERPY_API_KEY", ""),
            "provider": os.getenv("PEPPERPY_PROVIDER", "openrouter"),
        },
    )
    llm = HuggingFaceLLM(llm_config)
    await llm.initialize()

    # Initialize embedding manager
    embedding_config = EmbeddingConfig(
        model_name=os.getenv("PEPPERPY_MODEL", "google/gemini-2.0-flash-exp:free"),
        batch_size=32,
        cache_embeddings=True,
    )
    embedding_manager = EmbeddingManager(llm, embedding_config)

    # Example texts
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Pack my box with five dozen liquor jugs",
        "How vexingly quick daft zebras jump",
    ]

    try:
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = cast(list[list[float]], await embedding_manager.get_embeddings(texts))
        
        # Print embedding dimensions
        print(f"\nGenerated {len(embeddings)} embeddings")
        print(f"Each embedding has {len(embeddings[0])} dimensions")
        
        # Generate embedding for a single text
        single_text = "The quick brown fox"
        print("\nGenerating embedding for single text...")
        single_embedding = cast(list[float], await embedding_manager.get_embeddings(single_text))
        print(f"Single embedding has {len(single_embedding)} dimensions")

    finally:
        # Cleanup
        await embedding_manager.cleanup()
        await llm.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 