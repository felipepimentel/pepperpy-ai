"""Basic chat example."""

import asyncio
from typing import NoReturn

from pepperpy_ai.examples.utils import ExampleAIClient


async def main() -> NoReturn:
    """Run example."""
    # Create client
    client = ExampleAIClient()

    # Initialize
    await client.initialize()

    try:
        while True:
            # Get user input
            prompt = input("\nYou: ")
            if prompt.lower() in ["exit", "quit"]:
                break

            # Get response
            response = await client.complete(prompt)
            print(f"\nAssistant: {response.content}")

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
