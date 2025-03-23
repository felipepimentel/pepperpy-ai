"""Example of using agents with different personalities in PepperPy.

This example demonstrates how to create agents with distinct personalities
and communication styles that work together to solve problems.
"""

import asyncio
import os
from typing import List

from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.llm.providers.openrouter import OpenRouterProvider


async def main() -> None:
    """Run the example."""
    # Load environment variables
    load_dotenv()

    # Initialize LLM provider
    llm = OpenRouterProvider(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="anthropic/claude-3-opus-20240229",
    )

    # Create agent group
    group_id = await create_agent_group(
        agents=[
            {
                "type": "assistant",
                "name": "optimist",
                "system_message": (
                    "You are an optimistic and enthusiastic team member who always "
                    "sees the positive side of things. You encourage others and "
                    "suggest creative solutions to problems. Your communication style "
                    "is energetic and uplifting."
                ),
            },
            {
                "type": "assistant",
                "name": "pragmatist",
                "system_message": (
                    "You are a practical and analytical team member who focuses on "
                    "facts and feasibility. You help ground discussions in reality "
                    "and ensure plans are achievable. Your communication style is "
                    "clear and direct."
                ),
            },
            {
                "type": "assistant",
                "name": "innovator",
                "system_message": (
                    "You are an innovative and forward-thinking team member who "
                    "loves exploring new ideas. You challenge conventional thinking "
                    "and propose unique approaches. Your communication style is "
                    "imaginative and thought-provoking."
                ),
            },
            {
                "type": "user",
                "name": "facilitator",
                "system_message": (
                    "You are a team facilitator who guides discussions and ensures "
                    "all perspectives are considered. Help the team work together "
                    "effectively."
                ),
            },
        ],
        name="diverse_team",
        llm_config=llm.config,
        use_group_chat=True,
        max_rounds=12,
    )

    try:
        # Present the challenge
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Our company needs to improve employee engagement and productivity "
                "while maintaining a healthy work-life balance. What strategies "
                "would you recommend?"
            ),
        )

        # Print discussion
        print("\nTeam Discussion:")
        for msg in messages:
            print(f"\n{msg.role}: {msg.content}")

        # Follow up on specific ideas
        messages = await execute_task(
            group_id=group_id,
            task=(
                "The flexible work hours suggestion is interesting. How could we "
                "implement this while ensuring team collaboration remains strong?"
            ),
        )

        print("\nImplementation Discussion:")
        for msg in messages:
            print(f"\n{msg.role}: {msg.content}")

        # Create action plan
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Great discussion! Can you work together to create a concrete "
                "3-month action plan incorporating the best ideas from everyone?"
            ),
        )

        print("\nAction Plan:")
        for msg in messages:
            print(f"\n{msg.role}: {msg.content}")

    finally:
        # Clean up resources
        await cleanup_group(group_id)


if __name__ == "__main__":
    asyncio.run(main()) 