"""Simple example demonstrating LLM usage."""

import asyncio
import os

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

    try:
        # Generate text
        prompt = "The quick brown fox"
        print(f"\nGenerating text for prompt: {prompt}")
        response = await llm.generate(prompt, max_tokens=20)
        print(f"\nGenerated text: {response.text}")
        print(f"Tokens used: {response.tokens_used}")
        print(f"Model used: {response.model_name}")

        # Stream text
        print("\nStreaming text generation...")
        async for chunk in llm.generate_stream(prompt, max_tokens=20):
            print(chunk, end="", flush=True)
        print("\n")

    finally:
        # Cleanup
        await llm.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 