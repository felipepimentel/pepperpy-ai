"""Streaming example."""

import asyncio
from typing import cast

from pepperpy_ai.examples.utils import ExampleAIClient
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.providers.config import ProviderConfig
from pepperpy_ai.providers.openai import OpenAIProvider


async def main() -> None:
    """Run example."""
    # Create client with OpenAI provider
    provider = cast(type[BaseProvider[ProviderConfig]], OpenAIProvider)
    client = ExampleAIClient(provider=provider)

    # Initialize
    await client.initialize()

    try:
        while True:
            # Get user input
            prompt = input("\nYou: ")

            if not prompt:
                continue

            if prompt.lower() in ["exit", "quit"]:
                break

            # Create message
            messages = [{"content": prompt, "role": "user"}]

            # Stream responses
            print("\nAssistant: ", end="", flush=True)
            async for response in client.stream(messages):
                print(response["content"], end="", flush=True)
            print("\n")

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
