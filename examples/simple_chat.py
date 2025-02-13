"""Simple chat example using Pepperpy.

This example demonstrates how to create a simple chat application
using Pepperpy's simplified API.
"""

import asyncio

from pepperpy import Pepperpy


async def main() -> None:
    """Run the chat example."""
    # Create Pepperpy instance with auto-configuration
    pepper = await Pepperpy.create()

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

        # Get response using simplified chat method
        print("\nAssistant: ", end="", flush=True)
        response = await pepper.ask(message)
        print(response)
        print()  # New line after response

        # Small pause between messages
        await asyncio.sleep(1)

    print("-" * 50)
    print("Example chat completed!")

    # Interactive chat mode example
    print("\nStarting interactive chat mode...")
    print("(Press Ctrl+C to exit)")
    try:
        await pepper.chat(
            "Hi! Let's have a conversation."
        )  # Start interactive chat with greeting
    except KeyboardInterrupt:
        print("\nChat session ended.")


if __name__ == "__main__":
    asyncio.run(main())
