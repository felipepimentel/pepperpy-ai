"""Simple chat example using Pepperpy.

This example demonstrates how to create a simple chat application
using Pepperpy's simplified API.
"""

import asyncio

from pepperpy import PepperpyClient


async def main():
    """Run the chat example."""
    # Create client (automatically loads from environment)
    async with PepperpyClient() as client:
        print("Chat started! Type 'exit' to quit.")
        print("-" * 50)

        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "exit":
                break

            # Stream the response
            print("\nAssistant: ", end="", flush=True)
            async for chunk in client.chat_stream(user_input):
                print(chunk, end="", flush=True)
            print()  # New line after response


if __name__ == "__main__":
    asyncio.run(main())
