"""Example of simplified AI Gateway workflow usage with corrected imports."""

import asyncio
import uuid

from pepperpy.core.base import PepperpyError
from plugins.workflow.ai_gateway.gateway import (
    GatewayRequest,
    GatewayStatus,
)
from plugins.workflow.ai_gateway.run_mesh import MockModelProvider


async def simple_example() -> None:
    """Simple chat example with mock provider."""
    # Create a mock provider directly
    provider = MockModelProvider(model_id="mock-gpt")
    await provider.initialize()

    try:
        # Create a request with request ID and target
        request = GatewayRequest(
            request_id=str(uuid.uuid4()),
            operation="chat",
            target="mock-gpt",  # Required field
            parameters={
                "messages": [
                    {"role": "user", "content": "What is the capital of France?"}
                ]
            },
        )

        # Execute the request
        response = await provider.execute(request)

        # Print the result
        if response.status == GatewayStatus.SUCCESS:
            print(f"Chat Response: {response.outputs}")
        else:
            print(f"Error: {response.error}")
    finally:
        await provider.cleanup()


async def main() -> None:
    """Run the example."""
    try:
        await simple_example()
    except PepperpyError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
