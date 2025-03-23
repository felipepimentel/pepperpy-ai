"""Example usage of the agents module."""

import asyncio
import os
from typing import List

from pepperpy.agents import AgentFactory, Message, SimpleMemory
from pepperpy.llm.providers.openrouter import OpenRouterProvider


async def main():
    """Run the example."""
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")

    # Create LLM provider
    llm = OpenRouterProvider(api_key=api_key)
    await llm.initialize()

    # Create memory
    memory = SimpleMemory()

    # Create agent factory
    factory = AgentFactory()

    # Create a single agent
    agent = factory.create_agent(llm_provider=llm, memory=memory)
    await agent.initialize()

    # Execute a task with the agent
    messages = await agent.execute_task(
        "What are the three most significant developments in quantum computing in the past year?"
    )
    print_messages("Single Agent Response:", messages)

    # Create an agent group
    group = factory.create_group(
        llm_provider=llm,
        group_config={
            "agents": [
                {
                    "name": "researcher",
                    "role": "assistant",
                    "description": "Researches and analyzes information",
                },
                {
                    "name": "critic",
                    "role": "assistant",
                    "description": "Reviews and critiques information",
                },
            ]
        },
        memory=memory,
    )
    await group.initialize()

    # Execute a task with the group
    messages = await group.execute_task(
        "Analyze the potential impact of quantum computing on cryptography."
    )
    print_messages("Agent Group Response:", messages)

    # Get all messages from memory
    all_messages = await memory.get_messages()
    print_messages("All Messages in Memory:", all_messages)


def print_messages(title: str, messages: List[Message]) -> None:
    """Print a list of messages with a title.
    
    Args:
        title: Title to print before the messages.
        messages: List of messages to print.
    """
    print(f"\n{title}")
    print("-" * len(title))
    for msg in messages:
        print(f"{msg.role}: {msg.content}")


if __name__ == "__main__":
    asyncio.run(main()) 