"""Basic chat example."""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from pepperpy.providers.factory import create_provider
from pepperpy.types import Message


def load_environment() -> None:
    """Load environment variables from .env file."""
    if Path(".env").exists():
        load_dotenv()
    elif Path("../.env").exists():
        load_dotenv("../.env")


async def main() -> None:
    """Run example."""
    # Load environment variables
    load_environment()

    # Create provider
    provider = create_provider(name="openai", prefix="PEPPERPY_")

    try:
        # Initialize provider
        await provider.initialize()

        # Create messages
        messages: list[Message] = [
            {"content": "Hello! How are you?", "role": "user"},
        ]

        # Stream responses
        print("\nAssistant: ", end="", flush=True)
        async for response in await provider.stream(messages=messages):
            print(response["content"], end="", flush=True)
        print("\n")

    finally:
        # Clean up provider
        await provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
