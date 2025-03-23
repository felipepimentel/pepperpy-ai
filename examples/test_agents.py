"""Test the agents module with configured credentials."""

import asyncio
import os
from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.llm.providers.openrouter import OpenRouterProvider

async def main():
    # Load environment variables
    load_dotenv()

    # Get API key
    api_key = os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OpenRouter API key not found in environment variables")

    # Create LLM configuration with only supported fields
    llm_config = {
        "model": "openai/gpt-3.5-turbo",
        "api_key": api_key,
        "temperature": 0.7,
        "base_url": "https://openrouter.ai/api/v1",
        "default_headers": {
            "HTTP-Referer": "https://github.com/pimentel/pepperpy",
            "X-Title": "PepperPy Framework",
        }
    }

    try:
        # Create agent group with proper llm_config
        group_id = await create_agent_group(
            agents=[
                {
                    "type": "assistant",
                    "name": "researcher",
                    "system_message": "You are a research assistant specialized in AI and technology.",
                },
                {
                    "type": "user",
                    "name": "user",
                    "system_message": "You are the user requesting information.",
                }
            ],
            name="research_team",
            llm_config=llm_config,
        )

        print(f"Created agent group with ID: {group_id}")

        # Execute task
        messages = await execute_task(
            group_id=group_id,
            task="What are the three most significant recent developments in quantum computing? Provide a brief summary for each.",
            llm_config=llm_config,  # Pass the same llm_config
        )

        # Process messages
        print("\nConversation:")
        for msg in messages:
            print(f"\n{msg.role}: {msg.content}")

    except Exception as e:
        print(f"Error: {str(e)}")
        if hasattr(e, "__cause__") and e.__cause__:
            print(f"Caused by: {str(e.__cause__)}")
    finally:
        # Clean up
        if "group_id" in locals():
            await cleanup_group(group_id)
            print("\nCleaned up agent group")

if __name__ == "__main__":
    asyncio.run(main()) 