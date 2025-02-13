"""Example demonstrating the chat functionality of Pepperpy.

This example shows how to:
1. Initialize Pepperpy with minimal configuration
2. Use different chat modes (basic, streaming, interactive)
3. Handle chat commands and history
"""

import asyncio

from pepperpy import Pepperpy


async def basic_chat():
    """Demonstrate basic question-answer functionality."""
    pepper = await Pepperpy.create()

    # Simple question-answer
    response = await pepper.ask("What is artificial intelligence?")
    print("\nBasic Q&A:")
    print("Q: What is artificial intelligence?")
    print(f"A: {response}")


async def streaming_chat():
    """Demonstrate streaming responses."""
    pepper = await Pepperpy.create()

    print("\nStreaming Response:")
    print("Q: Explain quantum computing")
    print("A: ", end="", flush=True)

    # Stream response token by token
    async for token in pepper.stream_response("Explain quantum computing"):
        print(token, end="", flush=True)
    print()


async def interactive_chat():
    """Demonstrate interactive chat session."""
    pepper = await Pepperpy.create()
    
    print("\nInteractive Chat:")
    print("Available commands:")
    print("  /help  - Show available commands")
    print("  /clear - Clear chat history")
    print("  /save  - Save conversation")
    print("  Ctrl+C to exit")
    
    # Start interactive session
    pepper.chat("Tell me about AI")


async def main():
    # Run different chat examples
    await basic_chat()
    await streaming_chat()
    await interactive_chat()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
