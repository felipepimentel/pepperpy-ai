"""Example demonstrating the simplified workflow-based research assistant.

This example shows how to use the new declarative workflow system
to run research tasks without dealing with low-level agent details.
It demonstrates both the high-level workflow API and a mock provider
for testing purposes.
"""

import asyncio
import json
import os
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pepperpy import Pepperpy
from pepperpy.monitoring import logger
from pepperpy.providers.base import (
    BaseProvider,
    Message,
    Response,
)

log = logger.bind(example="research_workflow")


class MockMessage(Message):
    """Mock message for testing."""

    def __init__(self, content: str, id: Optional[str] = None):
        """Initialize a mock message."""
        super().__init__(id=id or str(uuid4()), content=content)


class MockResponse(Response):
    """Mock response for testing."""

    def __init__(
        self,
        content: str,
        id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a mock response."""
        super().__init__(id=id or uuid4(), content=content, metadata=metadata or {})


class MockOpenRouterProvider(BaseProvider):
    """Mock OpenRouter provider for testing the workflow.

    This provider returns predefined responses for different types
    of prompts, making it useful for testing and examples.
    """

    async def initialize(self) -> None:
        """Initialize the mock provider."""
        await super().initialize()
        self._logger.info("Mock provider initialized")

    async def cleanup(self) -> None:
        """Clean up the mock provider."""
        await super().cleanup()
        self._logger.info("Mock provider cleaned up")

    async def send_message(self, message: str) -> Response:
        """Send a message and get a response.

        Args:
            message: Message to send.

        Returns:
            Response: Provider response.

        """
        self._ensure_initialized()
        response = await self.generate([MockMessage(content=message)])
        return response

    async def complete(
        self,
        prompt: str,
        *,
        kwargs: Dict[str, Any] | None = None,
    ) -> str | AsyncGenerator[str, None]:
        """Complete a prompt using the mock provider.

        Args:
        ----
            prompt: The prompt to complete
            kwargs: Additional provider-specific parameters

        Returns:
        -------
            Generated text or async generator of text chunks if streaming

        """
        self._ensure_initialized()
        response = await self.generate([MockMessage(content=prompt)], **(kwargs or {}))
        return response.content

    async def generate(self, messages: List[Message], **kwargs: Any) -> Response:
        """Generate a response from the mock provider.

        Args:
        ----
            messages: List of messages to generate from
            kwargs: Additional arguments to pass to the provider

        Returns:
        -------
            Generated response

        """
        self._ensure_initialized()

        # Get the last user message
        last_message = next((m for m in reversed(messages) if m.content), None)
        if not last_message:
            return MockResponse(content="No user message found")

        # Return different mock responses based on the prompt content
        prompt = last_message.content.lower()
        if "understand the following research topic" in prompt:
            content = json.dumps({
                "summary": """
                Large Language Models (LLMs) are revolutionizing scientific research
                through their ability to process and analyze vast amounts of scientific
                literature, assist in hypothesis generation, and accelerate the research
                process. Key concepts include natural language processing, transfer
                learning, and scientific reasoning capabilities.
                
                Recent developments show increasing adoption of LLMs in various
                scientific domains, from literature review automation to experimental
                design assistance. However, challenges remain around reproducibility,
                bias in training data, and the need for domain-specific validation.
                
                Future directions point towards more specialized scientific LLMs,
                improved integration with research workflows, and development of
                better evaluation frameworks for scientific applications.
                """
            })
        elif "find relevant academic sources" in prompt:
            content = json.dumps({
                "sources": [
                    "1. 'The Impact of Large Language Models on Scientific Discovery' (Smith et al., 2023) - Nature AI",
                    "2. 'Challenges and Opportunities in Scientific LLMs' (Brown et al., 2023) - Science",
                    "3. 'LLMs as Research Assistants: A Systematic Review' (Johnson et al., 2024) - AI Review",
                    "4. 'Domain Adaptation of LLMs for Scientific Tasks' (Lee et al., 2023) - NeurIPS",
                    "5. 'Reproducibility Challenges in LLM-assisted Research' (Garcia et al., 2024) - arXiv",
                ]
            })
        else:
            content = json.dumps({
                "recommendations": """
                Based on the analyzed sources, several key recommendations emerge:

                1. Integration Strategy: Scientific workflows should carefully integrate
                   LLMs with existing research methodologies, ensuring reproducibility
                   and validation.

                2. Domain Adaptation: Development of specialized models and fine-tuning
                   approaches for specific scientific domains is crucial.

                3. Validation Frameworks: Establishment of robust validation protocols
                   for LLM-assisted scientific research is needed.

                4. Collaborative Approach: Encouraging collaboration between AI researchers
                   and domain scientists to address field-specific challenges.

                Future research should focus on developing standardized evaluation
                metrics, improving model interpretability, and creating domain-specific
                benchmarks for scientific LLM applications.
                """
            })

        return MockResponse(content=content)

    async def stream(
        self, messages: List[Message], **kwargs: Any
    ) -> AsyncIterator[Response]:
        """Stream responses from the mock provider.

        Args:
            messages: List of messages to generate from
            kwargs: Additional arguments to pass to the provider

        Returns:
            AsyncIterator[Response]: Stream of responses

        Raises:
            NotImplementedError: Streaming not supported by mock provider

        """
        self._ensure_initialized()
        response = await self.generate(messages, **kwargs)
        yield response

    async def chat_completion(
        self,
        model: str,
        messages: List[Message],
        **kwargs: Any,
    ) -> Response:
        """Generate a chat completion response.

        Args:
            model: Model to use for completion
            messages: List of messages for the conversation
            kwargs: Additional keyword arguments

        Returns:
            Response: Generated response

        """
        self._ensure_initialized()
        return await self.generate(messages, **kwargs)


async def main() -> None:
    """Run the research workflow example."""
    # Create Pepperpy instance with API key
    api_key = os.getenv("PEPPERPY_API_KEY")
    async with await Pepperpy.create(api_key=api_key) as pepper:
        # Simple question
        result = await pepper.ask("What is artificial intelligence?")
        print("\nQuick Answer:")
        print(result)

        # Research with detailed results
        result = await pepper.research("Impact of AI in Healthcare")
        print("\nResearch Summary:")
        print(result.tldr)

        print("\nKey Points:")
        for point in result.bullets:
            print(f"- {point}")

        print("\nReferences:")
        for ref in result.references:
            print(f"- {ref['title']} ({ref['url']})")

        # Using a team
        team = await pepper.hub.team("research-team")
        async with team.run("Analyze recent AI developments") as session:
            while session.current_step:
                print(f"\nCurrent Step: {session.current_step}")
                print(f"Progress: {session.progress * 100:.0f}%")

                if session.needs_input:
                    value = input(f"{session.input_prompt}: ")
                    session.provide_input(value)

                await asyncio.sleep(1)  # Wait for progress

            print("\nTeam Results:")
            print(session.step_results)


def run_sync() -> None:
    """Run the workflow synchronously.

    This is a convenience wrapper for users who don't want to deal
    with async/await syntax directly.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorkflow execution cancelled by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise


if __name__ == "__main__":
    run_sync()
