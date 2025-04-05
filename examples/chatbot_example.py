"""
Interactive chatbot example using OpenAI.

This example demonstrates how to create a simple interactive chatbot using
the PepperPy framework with streaming responses.

Requirements:
    - An OpenAI API key set in the OPENAI_API_KEY environment variable
"""

import asyncio
import os
import sys

from pepperpy import PepperPy
from pepperpy.llm import Message, OpenAIProvider


async def main() -> None:
    """Run the interactive chatbot example."""
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

    # Create the conversation history
    messages: list[Message | dict[str, str]] = [
        Message(
            role="system",
            content="You are a helpful assistant named PepperBot. You are powered by the PepperPy framework, a modular AI application framework with a vertical domain architecture. Keep your responses concise.",
        )
    ]

    # Welcome message
    print("\n===== PepperBot Chat =====")
    print("Type 'exit' or 'quit' to end the conversation")
    print("===========================\n")

    # Main chat loop
    while True:
        # Get user input
        user_input = input("You: ")

        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye! Have a great day!")
            break

        # Add user message to history
        messages.append(Message(role="user", content=user_input))

        # Print assistant indicator
        print("PepperBot: ", end="", flush=True)

        # Stream the response
        assistant_message = ""
        async for chunk in pepper.llm.stream_chat(messages):
            print(chunk, end="", flush=True)
            assistant_message += chunk

        # Add assistant response to history
        messages.append(Message(role="assistant", content=assistant_message))

        # Print newline after response
        print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nChat ended by user. Goodbye!")
        sys.exit(0)
