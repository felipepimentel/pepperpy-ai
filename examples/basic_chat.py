"""Basic chat example using PepperPy AI."""

import asyncio
import sys
from typing import NoReturn

from pepperpy_ai.ai_types import Message, MessageRole
from pepperpy_ai.exceptions import DependencyError
from pepperpy_ai.providers.config import ProviderSettings
from pepperpy_ai.providers.exceptions import ProviderError
from pepperpy_ai.providers.factory import create_provider


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
                "\nError: Missing or invalid API key. Please check your environment variables.\n",
                file=sys.stderr,
            )
            settings = ProviderSettings.from_env(prefix="PEPPERPY_")
            print(settings.get_env_help(prefix="PEPPERPY_"), file=sys.stderr)
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
        # Create provider from environment variables
        provider = create_provider(prefix="PEPPERPY_")
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
