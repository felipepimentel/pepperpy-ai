"""
LLM completion example using OpenAI.

This example demonstrates how to use the PepperPy framework to interact with OpenAI's LLM.

Requirements:
    - An OpenAI API key set in the OPENAI_API_KEY environment variable
    - The pepperpy-llm-openai plugin installed
"""

import asyncio
import os

from pepperpy.facade import PepperPyFacade
from pepperpy.llm import Message

# Import the provider from the plugin if you want to use it directly
# from plugins.llm.openai.pepperpy_llm_openai import OpenAIProvider
# Or install the package and import it directly:
# from pepperpy_llm_openai import OpenAIProvider


async def main() -> None:
    """Run the LLM completion example."""
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    # Configure PepperPyFacade with OpenAI provider by name
    # This is the low-level facade for direct provider access
    pepper_facade = PepperPyFacade()
    pepper_facade.with_llm(
        "openai",  # This will automatically load the OpenAI plugin
        api_key=api_key,
        model="gpt-3.5-turbo",  # You can change this to any OpenAI model
    )

    # Alternative: use the provider class directly
    # pepper_facade.with_llm(
    #     OpenAIProvider,
    #     api_key=api_key,
    #     model="gpt-3.5-turbo"
    # )

    # Initialize (this is important for providers that need setup)
    await pepper_facade.initialize()

    # Create a list of messages for the conversation
    messages: list[Message | dict[str, str]] = [
        Message(role="system", content="You are a helpful assistant."),
        Message(
            role="user", content="Hello, can you tell me about the PepperPy framework?"
        ),
    ]

    # Get a completion from the LLM using the chat method
    print("Sending request to OpenAI...")
    response = await pepper_facade.llm.chat(messages)

    # Print the response (chat returns a string)
    print("\nResponse from OpenAI:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
