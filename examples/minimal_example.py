"""Minimal example of using PepperPy.

This example demonstrates basic usage of the PepperPy framework
with minimal configuration.
"""

import asyncio

from pepperpy import PepperPy


async def main() -> None:
    """Run minimal example."""
    print("Minimal Example")
    print("=" * 50)

    # Initialize PepperPy with LLM support directly using provider name
    async with PepperPy().with_llm("openrouter") as pepper:
        # Generate text using chat interface
        response = await pepper.chat.with_user("Say hello!").generate()
        print("\nChat response:")
        print(response.content)

        # Generate text using text interface
        response = await pepper.text.with_prompt("Write a haiku about AI").generate()
        print("\nText response:")
        print(response)


if __name__ == "__main__":
    asyncio.run(main())
