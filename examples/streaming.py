"""Streaming example."""

import asyncio
from typing import NoReturn

from pepperpy_ai.examples.utils import ExampleAIClient
from pepperpy_ai.providers.openai import OpenAIProvider


async def main() -> None:
    """Run example."""
    # Create client
    client = ExampleAIClient(provider=OpenAIProvider)

    # Initialize
    await client.initialize()

    try:
        while True:
            # Get user input
            prompt = input("\nYou: ")
            if prompt.lower() in ["exit", "quit"]:
                break

            # Stream response
            print("\nAssistant: ", end="", flush=True)
            async for chunk in client.stream(prompt):
                print(chunk.content, end="", flush=True)
            print()

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
