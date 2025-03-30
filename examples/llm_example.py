"""Example usage of PepperPy's LLM capabilities."""

import asyncio
import os
from collections.abc import AsyncIterator

from loguru import logger

from pepperpy import GenerationChunk, PepperPy


async def simple_chat() -> None:
    """Demonstrate simple chat interaction."""
    async with PepperPy().with_llm(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo",
    ) as pepper:
        # Simple single message
        result = await pepper.chat.with_user(
            "What is the capital of France?"
        ).generate()
        print(f"\nSimple response: {result.content}")

        # Multi-message conversation with system prompt
        result = await (
            pepper.chat.with_system("You are a helpful geography teacher.")
            .with_user("What are the three largest cities in Brazil?")
            .with_temperature(0.7)
            .generate()
        )
        print(f"\nConversation response: {result.content}")

        # Show token usage
        if result.usage:
            print("\nToken usage:")
            print(f"  Prompt tokens: {result.usage['prompt_tokens']}")
            print(f"  Completion tokens: {result.usage['completion_tokens']}")
            print(f"  Total tokens: {result.usage['total_tokens']}")


async def streaming_chat() -> None:
    """Demonstrate streaming chat interaction."""
    async with PepperPy().with_llm(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo",
    ) as pepper:
        print("\nStreaming response:")
        chunks: AsyncIterator[GenerationChunk] = await (
            pepper.chat.with_system("You are a creative storyteller.")
            .with_user("Tell me a short story about a magical forest.")
            .with_temperature(0.8)
            .stream()
        )

        async for chunk in chunks:
            print(chunk.content, end="", flush=True)
        print()  # New line after story


async def main() -> None:
    """Run the examples."""
    try:
        await simple_chat()
        await streaming_chat()
    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
