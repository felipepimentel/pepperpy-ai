"""Example AI Gateway workflow using real providers.

This example demonstrates using the AI Gateway adapter directly
with real providers for testing or development.
"""

import asyncio
import os

from plugins.workflow.ai_gateway.adapter import AIGatewayAdapter


async def run_example() -> None:
    """Simple chat example with provider."""
    # Get provider type from environment variable or use default
    provider_type = os.environ.get("PEPPERPY_LLM_PROVIDER", "openai")
    model_id = os.environ.get("PEPPERPY_LLM_MODEL", "gpt-3.5-turbo")

    print(
        f"Creating AIGatewayAdapter with provider_type={provider_type}, model_id={model_id}"
    )

    # Use the adapter pattern
    async with AIGatewayAdapter(
        provider_type=provider_type, model_id=model_id
    ) as adapter:
        # Create a chat request
        result = await adapter.execute(
            {
                "operation": "chat",
                "target": model_id,  # Required field
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Tell me about PepperPy framework."},
                ],
            }
        )

        print("\nChat Result:")
        print(f"Status: {result.get('status')}")
        if result.get("status") == "success":
            print(f"Response: {result.get('data', {}).get('message')}")
        else:
            print(f"Error: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(run_example())
