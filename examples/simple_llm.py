"""Simple example demonstrating LLM usage."""

import asyncio
import os

from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig


async def main() -> None:
    """Run the example."""
    # Create LLM config
    llm_config = LLMConfig(
        api_key=os.environ["HUGGINGFACE_API_KEY"],
        model="meta-llama/Llama-2-70b-chat-hf",
        base_url="https://api-inference.huggingface.co/models"
    )
    
    # Initialize LLM
    llm = HuggingFaceProvider(llm_config.to_dict())
    await llm.initialize()

    try:
        # Generate text
        prompt = "What is the meaning of life?"
        print(f"\nGenerating text for prompt: {prompt}")
        response = await llm.generate(prompt)
        print(f"\nGenerated text: {response}")

        # Stream text
        print("\nStreaming text generation...")
        async for chunk in llm.generate_stream(prompt):
            print(chunk, end="", flush=True)
        print("\n")

    finally:
        # Cleanup
        await llm.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 