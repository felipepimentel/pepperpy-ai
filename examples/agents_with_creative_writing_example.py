"""Example of using agents for collaborative creative writing in PepperPy.

This example demonstrates how to create a group of agents that work together
to write creative content, with streaming responses for real-time feedback.
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, List, Union

from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.agents.provider import Message
from pepperpy.llm.providers.openrouter import OpenRouterProvider


async def print_stream(messages: Union[List[Message], AsyncGenerator[Message, None]]) -> None:
    """Print messages or a stream of messages with appropriate formatting.

    Args:
        messages: List of messages or generator yielding message chunks
    """
    if isinstance(messages, list):
        for msg in messages:
            print(f"\n{msg.role}: {msg.content}")
    else:
        current_role = None
        async for msg in messages:
            if msg.role != current_role:
                if current_role is not None:
                    print()  # New line between different roles
                print(f"{msg.role}: ", end="", flush=True)
                current_role = msg.role
            print(msg.content, end="", flush=True)
        print("\n")  # Final new line


async def main() -> None:
    """Run the example."""
    # Load environment variables
    load_dotenv()

    # Initialize LLM provider with streaming enabled
    llm = OpenRouterProvider(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="anthropic/claude-3-opus-20240229",
        config={"stream": True},
    )

    # Create agent group
    group_id = await create_agent_group(
        agents=[
            {
                "type": "assistant",
                "name": "story_architect",
                "system_message": (
                    "You are a creative story architect who excels at developing "
                    "engaging plot structures and story outlines. You help ensure "
                    "the story has a strong foundation with proper pacing, character "
                    "arcs, and thematic elements."
                ),
                "config": {"stream": True},
            },
            {
                "type": "assistant",
                "name": "character_writer",
                "system_message": (
                    "You are a character-focused writer who specializes in creating "
                    "deep, believable characters with distinct voices and personalities. "
                    "You help develop character dialogue and interactions that feel "
                    "authentic and drive the story forward."
                ),
                "config": {"stream": True},
            },
            {
                "type": "assistant",
                "name": "prose_stylist",
                "system_message": (
                    "You are a prose stylist with a talent for vivid descriptions "
                    "and engaging narrative voice. You help polish the writing to "
                    "make it more evocative and impactful, while maintaining "
                    "consistency in tone and style."
                ),
                "config": {"stream": True},
            },
            {
                "type": "user",
                "name": "editor",
                "system_message": (
                    "You are the editor guiding the creative process. You provide "
                    "the initial concept and help shape the story through feedback "
                    "and suggestions."
                ),
            },
        ],
        name="writing_team",
        llm_config=llm.config,
        use_group_chat=True,
        max_rounds=20,
    )

    try:
        # Start with story concept
        print("\nDeveloping Story Concept...")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Let's create a short story about a time traveler who discovers "
                "their actions in the past are actually creating the future they "
                "were trying to prevent. We need:\n"
                "1. A basic plot outline\n"
                "2. Main character details\n"
                "3. Key story beats\n"
                "Please collaborate to develop these elements."
            ),
            stream=True,
        )
        await print_stream(messages)

        # Develop first scene
        print("\nWriting Opening Scene...")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Based on our outline, let's write the opening scene. We should:\n"
                "1. Introduce the protagonist and their motivation\n"
                "2. Set up the time travel element\n"
                "3. Plant subtle hints about the paradox\n"
                "Each of you focus on your specialties while maintaining a "
                "cohesive narrative voice."
            ),
            stream=True,
        )
        await print_stream(messages)

        # Add a plot twist
        print("\nDeveloping Plot Twist...")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Now let's develop the crucial moment where the protagonist "
                "realizes their role in creating the future. Focus on:\n"
                "1. The emotional impact of the revelation\n"
                "2. How this changes their perspective\n"
                "3. The implications for their next actions\n"
                "Make this revelation both surprising and inevitable."
            ),
            stream=True,
        )
        await print_stream(messages)

        # Write the conclusion
        print("\nCrafting the Conclusion...")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Let's bring the story to a satisfying conclusion that:\n"
                "1. Resolves the time travel paradox\n"
                "2. Completes the protagonist's character arc\n"
                "3. Delivers the story's thematic message\n"
                "Work together to make this ending both meaningful and memorable."
            ),
            stream=True,
        )
        await print_stream(messages)

    finally:
        # Clean up resources
        await cleanup_group(group_id)


if __name__ == "__main__":
    asyncio.run(main()) 