"""
LLM streaming example using OpenAI.

This example demonstrates how to use the PepperPy framework to stream responses from OpenAI.

Requirements:
    - An OpenAI API key set in the OPENAI_API_KEY environment variable
"""

import asyncio
import os

from pepperpy import PepperPy
from pepperpy.llm import Message, OpenAIProvider


async def main() -> None:
    """Run the LLM streaming example."""
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    # Configure PepperPy with OpenAI provider
    pepper = PepperPy()
    pepper.with_llm(
        OpenAIProvider,
        api_key=api_key,
        model="gpt-3.5-turbo",  # You can change this to any OpenAI model
    )

    # Initialize (this is important for providers that need setup)
    await pepper.initialize()

    # Create a list of messages for the conversation
    messages: list[Message | dict[str, str]] = [
        Message(role="system", content="You are a helpful assistant."),
        Message(
            role="user",
            content="Write a short story about a robot discovering emotions.",
        ),
    ]

    # Stream the response from the LLM
    print("Streaming response from OpenAI...\n")

    # We'll print the response token by token as it streams
    async for chunk in pepper.llm.stream_chat(messages):
        # Print without newline and flush to show streaming effect
        print(chunk, end="", flush=True)

    # Print a final newline
    print("\n\nStreaming complete.")


if __name__ == "__main__":
    asyncio.run(main())
