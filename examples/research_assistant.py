"""Example demonstrating the research assistant agent."""

import asyncio
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from pydantic import SecretStr

from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.messages import Message
from pepperpy.providers.services.openrouter import OpenRouterConfig, OpenRouterProvider


async def main():
    """Run a research task using the research assistant agent."""
    try:
        # Load environment variables
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)

        # Create provider configuration
        provider_config = OpenRouterConfig(
            provider_type="openrouter",
            api_key=SecretStr(os.getenv("PEPPERPY_API_KEY", "")),
            model=os.getenv("PEPPERPY_MODEL", "openai/gpt-4"),
            temperature=float(os.getenv("PEPPERPY_AGENT__TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("PEPPERPY_AGENT__MAX_TOKENS", "2048")),
            timeout=float(os.getenv("PEPPERPY_AGENT__TIMEOUT", "30.0")),
            max_retries=3,
        )

        # Create provider
        provider = OpenRouterProvider(config=provider_config)
        await provider.initialize()

        try:
            # Run research assistant
            messages = [
                Message(
                    id=str(uuid4()),
                    content="Analyze the current state and future trends of AI in Healthcare",
                    metadata={"role": "user"},
                )
            ]
            result = await provider.generate(messages)
            print(result.content)

        finally:
            # Clean up provider resources
            await provider.cleanup()

    except (ConfigurationError, StateError) as e:
        print(f"Configuration/State Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
