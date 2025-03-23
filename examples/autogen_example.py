"""Example demonstrating the usage of AutoGen provider in PepperPy."""

import asyncio
import os
from typing import List

from pepperpy.agents.provider import Message
from pepperpy.agents.providers.autogen import AutoGenConfig, AutoGenProvider


async def run_example() -> None:
    """Run the AutoGen provider example."""
    # Initialize provider with configuration
    config = AutoGenConfig(
        name="code_assistant",
        description="An AI assistant that helps with coding tasks",
        llm_config={
            "config_list": [
                {
                    "model": "gpt-4",
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                }
            ],
            "temperature": 0,
        },
        assistant_config={
            "name": "coding_assistant",
            "system_message": (
                "You are a helpful AI coding assistant. "
                "You help users write clean, efficient, and well-documented code."
            ),
            "human_input_mode": "NEVER",
        },
    )

    provider = AutoGenProvider()
    await provider.initialize(config)

    # Execute a coding task
    task = """
    Please help me write a Python function that:
    1. Takes a list of numbers as input
    2. Filters out all negative numbers
    3. Returns the sum of the remaining positive numbers
    """

    messages: List[Message] = await provider.execute(task)

    # Print the conversation
    print("\nConversation:")
    print("-" * 50)
    for msg in messages:
        print(f"\n{msg.role}: {msg.content}")
        print("-" * 50)

    # Clean up
    await provider.shutdown()


if __name__ == "__main__":
    asyncio.run(run_example())
