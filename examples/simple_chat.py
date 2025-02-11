"""Simple chat example using Pepperpy.

This example demonstrates how to create a simple chat application
using Pepperpy's simplified API.
"""

import asyncio

from pepperpy import PepperpyClient
from pepperpy.core.config import PepperpyConfig


async def main() -> None:
    """Run the chat example."""
    # Create configuration with default settings
    config = PepperpyConfig()

    # Create client with configuration
    async with PepperpyClient(config=config) as client:
        print("Chat started! Running example messages...")
        print("-" * 50)

        # Example messages
        example_messages = [
            "Olá! Como você está?",
            "Me conte uma curiosidade interessante sobre tecnologia",
            "Explique de forma simples como funciona a inteligência artificial",
        ]

        for message in example_messages:
            # Show user message
            print(f"\nYou: {message}")

            # Get response from agent
            print("\nAssistant: ", end="", flush=True)
            response = await client.send_message(message)
            print(response)
            print()  # New line after response

            # Small pause between messages
            await asyncio.sleep(1)

        print("-" * 50)
        print("Example chat completed!")


if __name__ == "__main__":
    asyncio.run(main())
