#!/usr/bin/env python
"""Simple example of using the PepperPy LLM module for chat.

This example demonstrates how to use the PepperPy LLM module to chat with
a language model using the OpenAI provider.
"""

import asyncio
import os
from typing import List

from pepperpy.core.interfaces import ProviderConfig
from pepperpy.llm import (
    ChatOptions,
    Message,
    create_provider,
)


async def main():
    """Run the example."""
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    # Create provider configuration
    config = ProviderConfig(
        provider_type="openai",
        settings={
            "api_key": api_key,
        },
    )

    # Create provider
    provider = create_provider(config)

    # Validate provider
    await provider.validate()

    # Get available models
    models = await provider.get_models()
    print(f"Available models: {len(models)}")
    for model in models[:5]:  # Show first 5 models
        print(f"  - {model.id} ({model.type.value}, {model.size.value})")

    # Create messages
    messages: List[Message] = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello, who are you?"),
    ]

    # Create options
    options = ChatOptions(
        temperature=0.7,
        max_tokens=100,
    )

    # Generate chat response
    print("\nGenerating chat response...")
    response = await provider.chat(messages, "gpt-3.5-turbo", options)

    # Print response
    print(f"\nAssistant: {response.message.content}")
    print(f"\nToken usage: {response.total_tokens} tokens")


if __name__ == "__main__":
    asyncio.run(main())
