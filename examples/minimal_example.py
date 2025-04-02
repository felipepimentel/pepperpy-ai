"""PepperPy Minimal Example

This example demonstrates basic usage of the PepperPy framework.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from pepperpy import PepperPy, init_framework
from pepperpy.core.errors import ProviderError

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def run_chat(pepper: PepperPy, prompt: str) -> Optional[str]:
    """Run a chat interaction safely.

    Args:
        pepper: PepperPy instance
        prompt: User prompt

    Returns:
        Generated response or None if error
    """
    try:
        response = await pepper.chat.with_user(prompt).generate()
        return response.content
    except ProviderError as e:
        print(f"Error generating response: {e}")
        return None


async def main() -> None:
    """Run the example."""
    print("PepperPy Minimal Example")
    print("=" * 50)

    try:
        # Initialize the framework
        await init_framework()

        # Create PepperPy instance with LLM provider
        pepper = PepperPy()
        await pepper.initialize()

        # Get API key from environment variable
        api_key = os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY")
        if not api_key:
            raise ProviderError("OpenRouter API key not found in environment variables")

        # Configure LLM provider
        pepper.with_llm(
            provider_type="openrouter",
            api_key=api_key,
            model="openai/gpt-4o-mini",
        )

        # Generate text using chat
        if response := await run_chat(
            pepper, "Tell me a joke about Python programming."
        ):
            print("\nJoke Response:")
            print(response)

        # Generate chat completion
        if response := await run_chat(pepper, "What is the capital of France?"):
            print("\nCapital Response:")
            print(response)

        # Clean up
        await pepper.cleanup()

    except Exception as e:
        print(f"Error running example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
