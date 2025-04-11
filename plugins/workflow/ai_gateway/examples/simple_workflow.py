"""Example of simplified AI Gateway workflow usage."""

import asyncio

from pepperpy.core.base import PepperpyError
from plugins.workflow.ai_gateway.base_workflow import BaseWorkflow


async def chat_example() -> None:
    """Simple chat example."""
    # Initialize with just chat capability
    async with BaseWorkflow(llm_provider="mock") as workflow:
        result = await workflow.execute_chat([
            {"role": "user", "content": "What is the capital of France?"}
        ])

        if result.success:
            print(f"Chat Response: {result.data}")
        else:
            print(f"Error: {result.error}")


async def rag_example() -> None:
    """Simple RAG example."""
    # Initialize with RAG capability
    async with BaseWorkflow(llm_provider="mock", use_rag=True) as workflow:
        result = await workflow.execute_rag(
            query="What does the document say about X?",
            context_path="path/to/context.pdf",
        )

        if result.success:
            print(f"RAG Response: {result.data}")
        else:
            print(f"Error: {result.error}")


async def vision_example() -> None:
    """Simple vision example."""
    # Initialize with vision capability
    async with BaseWorkflow(llm_provider="mock", use_vision=True) as workflow:
        result = await workflow.execute_vision(
            prompt="What's in this image?", image_path="path/to/image.jpg"
        )

        if result.success:
            print(f"Vision Response: {result.data}")
        else:
            print(f"Error: {result.error}")


async def tool_example() -> None:
    """Simple tool example."""
    # Initialize with specific tools
    async with BaseWorkflow(
        llm_provider="mock", tools=["calculator", "weather"]
    ) as workflow:
        # Use calculator tool
        calc_result = await workflow.execute_tool("calculator", {"expression": "2 + 2"})

        if calc_result.success:
            print(f"Calculator Result: {calc_result.data}")

        # Use weather tool
        weather_result = await workflow.execute_tool("weather", {"location": "London"})

        if weather_result.success:
            print(f"Weather Result: {weather_result.data}")


async def main() -> None:
    """Run all examples."""
    try:
        await chat_example()
        await rag_example()
        await vision_example()
        await tool_example()
    except PepperpyError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
