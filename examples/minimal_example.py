"""Example demonstrating a minimal PepperPy setup using fluent API.

This example shows how to use PepperPy's fluent API to create a simple LLM application.
"""

import asyncio

from pepperpy import PepperPy


async def main() -> None:
    """Run the example."""
    print("Minimal Example")
    print("=" * 50)

    async with PepperPy().with_llm() as pepper:
        response = await (
            pepper.chat
            .with_system("You are a helpful assistant.")
            .with_user("Hello, PepperPy!")
            .generate()
        )

        print(f"\nResponse: {response.content}")
        print(f"Tokens: {response.usage.get('total_tokens', 0) if response.usage else 0}")


if __name__ == "__main__":
    asyncio.run(main())
