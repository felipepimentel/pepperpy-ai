"""Example demonstrating the simplified workflow-based research assistant.

This example shows how to use the new declarative workflow system
to run research tasks without dealing with low-level agent details.
It demonstrates both the high-level workflow API and a mock provider
for testing purposes.
"""

import asyncio
import json
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Dict, List
from uuid import uuid4

from pepperpy import Pepperpy
from pepperpy.core.types import ResponseStatus
from pepperpy.monitoring import logger
from pepperpy.providers.base import (
    BaseProvider,
    Message,
    ProviderConfig,
    Response,
)

log = logger.bind(example="research_workflow")


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
        response = await self.generate(
            [Message(role="user", content=prompt)], **(kwargs or {})
        )
        return response.content["text"]

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
        last_message = next(
            (m for m in reversed(messages) if m["role"] == "user"), None
        )
        if not last_message:
            return Response(
                id=uuid4(),
                message_id=str(uuid4()),
                content={"text": "No user message found"},
                status=ResponseStatus.ERROR,
                metadata={},
            )

        # Return different mock responses based on the prompt content
        prompt = last_message["content"].lower()
        if "understand the following research topic" in prompt:
            content = {
                "text": json.dumps(
                    {
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
                    }
                )
            }
        elif "find relevant academic sources" in prompt:
            content = {
                "text": json.dumps(
                    {
                        "sources": [
                            "1. 'The Impact of Large Language Models on Scientific Discovery' (Smith et al., 2023) - Nature AI",
                            "2. 'Challenges and Opportunities in Scientific LLMs' (Brown et al., 2023) - Science",
                            "3. 'LLMs as Research Assistants: A Systematic Review' (Johnson et al., 2024) - AI Review",
                            "4. 'Domain Adaptation of LLMs for Scientific Tasks' (Lee et al., 2023) - NeurIPS",
                            "5. 'Reproducibility Challenges in LLM-assisted Research' (Garcia et al., 2024) - arXiv",
                        ]
                    }
                )
            }
        else:
            content = {
                "text": json.dumps(
                    {
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
                    }
                )
            }

        return Response(
            id=uuid4(),
            message_id=str(uuid4()),
            content=content,
            status=ResponseStatus.SUCCESS,
            metadata={},
        )

    def stream(self, messages: List[Message], **kwargs: Any) -> AsyncIterator[Response]:
        """Stream responses from the mock provider.

        Args:
        ----
            messages: List of messages to generate from
            kwargs: Additional arguments to pass to the provider

        Returns:
        -------
            AsyncIterator[Response]: Stream of responses

        """
        self._ensure_initialized()
        raise NotImplementedError("Streaming not supported by mock provider")

    async def chat_completion(
        self,
        model: str,
        messages: List[Message],
        **kwargs: Any,
    ) -> str:
        """Run a chat completion with the given parameters.

        Args:
        ----
            model: The model to use
            messages: The messages to send to the model
            **kwargs: Additional parameters for the model

        Returns:
        -------
            The model's response

        """
        self._ensure_initialized()
        response = await self.generate(messages, **kwargs)
        return response.content["text"]


async def main() -> None:
    """Run the research workflow example."""
    # Initialize Pepperpy with mock provider
    pepper = Pepperpy.init(
        storage_dir=".pepper_hub",
        provider_type="mock_openrouter",
        api_key="mock_key",
        model="mock/gpt-4",
    )

    # Register the mock provider
    from pepperpy.providers.engine import ProviderEngine

    mock_config = ProviderConfig(
        provider_type="mock_openrouter",
        api_key="mock_key",
        model="mock/gpt-4",
        temperature=0.7,
        max_tokens=1000,
    )

    engine = ProviderEngine()
    await engine.initialize()
    await engine.register_provider(MockOpenRouterProvider(mock_config))

    # Define research topic
    topic = "Large Language Models and their impact on scientific research"

    # Run the workflow
    try:
        # Load and run the workflow
        results = await pepper.hub.workflow_engine.run(
            workflow_name="research", input_data={"topic": topic, "max_sources": 5}
        )

        # Print results in a structured way
        print("\nResearch Results")
        print("=" * 80)

        print("\n1. Initial Analysis")
        print("-" * 40)
        print(results["summary"])

        print("\n2. Relevant Sources")
        print("-" * 40)
        for source in results["sources"]:
            print(source)

        print("\n3. Synthesized Findings")
        print("-" * 40)
        print(results["recommendations"])

        print("\n" + "=" * 80)

    except Exception as e:
        log.error("Workflow execution failed", error=str(e), topic=topic)
        raise


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
