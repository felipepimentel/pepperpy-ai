"""Basic chat example using PepperPy AI."""

import asyncio
import os
import sys
from typing import NoReturn

from pepperpy_ai.ai_types import Message, MessageRole
from pepperpy_ai.exceptions import DependencyError
from pepperpy_ai.providers.exceptions import ProviderError
from pepperpy_ai.providers.openai import OpenAIProvider


def get_api_key() -> str:
    """Get OpenAI API key from environment.
    
    Returns:
        str: API key

    Raises:
        SystemExit: If API key is not set
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print(
            "\nError: OPENAI_API_KEY environment variable is not set.\n"
            "Please set it with your OpenAI API key:\n\n"
            "    export OPENAI_API_KEY='your-api-key'\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def handle_error(error: Exception) -> NoReturn:
    """Handle error and exit.
    
    Args:
        error: Exception to handle
    """
    if isinstance(error, DependencyError):
        print(error, file=sys.stderr)
        sys.exit(1)
    elif isinstance(error, ProviderError):
        if "api_key" in str(error).lower():
            print(
                "\nError: Invalid OpenAI API key. Please check your API key and try again.\n",
                file=sys.stderr,
            )
        else:
            print(f"\nError: {error}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\nUnexpected error: {error}", file=sys.stderr)
        sys.exit(1)


async def main() -> None:
    """Run basic chat example."""
    provider = None
    try:
        # Get API key
        api_key = get_api_key()

        # Initialize provider with configuration
        provider = OpenAIProvider(
            config={
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 30.0,  # 30 seconds timeout
            },
            api_key=api_key,
        )
        await provider.initialize()

        # Send a message
        messages = [
            Message(role=MessageRole.USER, content="Hello! How are you?")
        ]

        print("\nUser: Hello! How are you?")
        print("\nAssistant: ", end="", flush=True)

        async for response in provider.stream(messages):
            print(response.content, end="", flush=True)
        print("\n")

    except Exception as e:
        handle_error(e)
    finally:
        if provider:
            await provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
