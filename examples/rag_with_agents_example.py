"""Example of using RAG with agents in PepperPy.

This example demonstrates how to combine RAG and agents to create an AI system
that can answer questions using both retrieved context and agent collaboration.
"""

import asyncio
import os
from typing import List

from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.llm.providers.openrouter import OpenRouterProvider
from pepperpy.rag.providers.supabase.provider import SupabaseProvider
from pepperpy.rag.providers.supabase.config import SupabaseConfig


async def main() -> None:
    """Run the example."""
    # Load environment variables
    load_dotenv()

    # Initialize providers
    llm = OpenRouterProvider(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="anthropic/claude-3-opus-20240229",
    )

    rag = SupabaseProvider(
        config=SupabaseConfig(
            url=os.getenv("SUPABASE_URL", ""),
            key=os.getenv("SUPABASE_KEY", ""),
            collection="documents",
        )
    )

    # Create agent group
    group_id = await create_agent_group(
        agents=[
            {
                "type": "assistant",
                "name": "researcher",
                "system_message": (
                    "You are a research assistant. Your role is to analyze the provided "
                    "context and help answer questions accurately based on the information."
                ),
            },
            {
                "type": "user",
                "name": "user",
                "system_message": (
                    "You are the user requesting information. Your role is to provide the "
                    "initial question and any follow-up questions needed."
                ),
            },
        ],
        name="research_team",
        llm_config=llm.config,
    )

    try:
        # Query the RAG system
        query = "What are the latest AI trends?"
        context = await rag.query(query)

        # Execute task with context
        messages = await execute_task(
            group_id=group_id,
            task=query,
            context={"documents": context},
        )

        # Print messages
        for msg in messages:
            print(f"{msg.role}: {msg.content}")

    finally:
        # Clean up resources
        await cleanup_group(group_id)
        await rag.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
