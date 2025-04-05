"""
LLM embedding example using OpenAI.

This example demonstrates how to use the PepperPy framework to generate embeddings with OpenAI.

Requirements:
    - An OpenAI API key set in the OPENAI_API_KEY environment variable
"""

import asyncio
import os

import numpy as np

from pepperpy import PepperPy
from pepperpy.llm import OpenAIProvider


async def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate the cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity (between -1 and 1)
    """
    # Convert to numpy arrays for easier calculation
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    # Calculate dot product and norms
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    # Compute the cosine similarity
    return dot_product / (norm_v1 * norm_v2)


async def main() -> None:
    """Run the embedding example."""
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    # Configure PepperPy with OpenAI provider
    pepper = PepperPy()
    pepper.with_llm(
        OpenAIProvider,
        api_key=api_key,
        # For embeddings, we'll use the text-embedding-ada-002 model by default
    )

    # Initialize the provider
    await pepper.initialize()

    # Example texts to embed
    text1 = "The quick brown fox jumps over the lazy dog."
    text2 = "A fast auburn fox leaps above the sleepy canine."
    text3 = "The weather today is sunny and warm."

    # Generate embeddings
    print("Generating embeddings...")
    embedding1 = await pepper.llm.embed(text1)
    embedding2 = await pepper.llm.embed(text2)
    embedding3 = await pepper.llm.embed(text3)

    # Print embedding dimensions
    print(f"\nEmbedding dimensions: {len(embedding1)}")

    # Calculate similarities between texts
    sim_1_2 = await cosine_similarity(embedding1, embedding2)
    sim_1_3 = await cosine_similarity(embedding1, embedding3)
    sim_2_3 = await cosine_similarity(embedding2, embedding3)

    # Print the results
    print("\nCosine similarities:")
    print(f"Text 1 & Text 2: {sim_1_2:.4f} (semantically similar)")
    print(f"Text 1 & Text 3: {sim_1_3:.4f} (semantically different)")
    print(f"Text 2 & Text 3: {sim_2_3:.4f} (semantically different)")


if __name__ == "__main__":
    asyncio.run(main())
