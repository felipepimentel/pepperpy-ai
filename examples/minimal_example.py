"""PepperPy Minimal Example

This example demonstrates basic usage of the PepperPy framework.
"""

import asyncio
import os
import sys
from pathlib import Path

from pepperpy import PepperPy, init_framework

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main() -> None:
    """Run the example."""
    print("PepperPy Minimal Example")
    print("=" * 50)

    # Initialize the framework
    await init_framework()

    # Create PepperPy instance with OpenRouter LLM provider
    pepper = PepperPy()
    await pepper.with_llm(
        "openrouter",
        api_key=os.environ.get("PEPPERPY_LLM__OPENROUTER_API_KEY"),
        model=os.environ.get("PEPPERPY_LLM__MODEL", "openai/gpt-4o-mini"),
        temperature=float(os.environ.get("PEPPERPY_LLM__TEMPERATURE", "0.7")),
        max_tokens=int(os.environ.get("PEPPERPY_LLM__MAX_TOKENS", "1024")),
    )

    # Generate text using chat
    response = await pepper.chat.with_user(
        "Tell me a joke about Python programming."
    ).generate()
    print(response.content)

    # Generate chat completion
    response = (
        await pepper.chat.with_system("You are a helpful assistant.")
        .with_user("What is the capital of France?")
        .generate()
    )
    print(response.content)

    # Clean up
    await pepper.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
