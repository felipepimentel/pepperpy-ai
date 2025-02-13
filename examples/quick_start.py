"""Example of using Pepperpy's quick start functionality."""

import asyncio

from pepperpy import Pepperpy


async def main() -> None:
    """Run the example."""
    # Start interactive setup if needed, or use environment variables
    pepper = await Pepperpy.create()

    # Simple question
    print("\n1. Simple Question Example:")
    print("-" * 50)
    result = await pepper.ask("What is artificial intelligence?")
    print(f"Response: {result}\n")

    # Research with structured output
    print("\n2. Research Example:")
    print("-" * 50)
    result = await pepper.research("Impact of AI in Healthcare")
    print("Summary:")
    print(result.tldr)  # Short summary
    print("\nKey Points:")
    print(result.bullets)  # Main points

    # Team collaboration example
    print("\n3. Team Collaboration Example:")
    print("-" * 50)
    team = await pepper.hub.team("research-team")
    async with team.run("Write an article about AI") as session:
        print(f"Current Step: {session.current_step}")
        print(f"Thoughts: {session.thoughts}")
        print(f"Progress: {session.progress}%")

        # Demonstrate intervention if needed
        if session.needs_input:
            session.provide_input("More details about AI applications")

    # Interactive chat mode
    print("\n4. Interactive Chat Mode:")
    print("-" * 50)
    print("Starting chat... (Press Ctrl+C to exit)")
    try:
        await pepper.chat(
            "Tell me about AI"
        )  # Start interactive chat with initial message
    except KeyboardInterrupt:
        print("\nChat session ended.")


if __name__ == "__main__":
    asyncio.run(main())
