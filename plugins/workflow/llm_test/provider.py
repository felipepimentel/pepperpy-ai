"""LLM test workflow provider implementation."""

import logging
from typing import Any

from pepperpy import PepperPy
from pepperpy.core.base import PepperpyError
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.workflow.decorators import workflow


class WorkflowError(PepperpyError):
    """Base error for workflow errors."""


@workflow(
    name="llm_test",
    description="Test workflow for LLM capabilities",
    version="0.1.0",
)
class LLMTestWorkflow(WorkflowProvider):
    """Test workflow for LLM capabilities."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration."""
        super().__init__(**kwargs)

        # Configuration values with defaults
        self.config = kwargs
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1000)

        # Initialize state
        self.initialized = False
        self.llm = None
        self.logger = logging.getLogger(__name__)
        self.pepperpy = None

    async def initialize(self) -> None:
        """Initialize resources."""
        if self.initialized:
            return

        try:
            # Initialize LLM provider
            self.pepperpy = PepperPy()
            self.llm = self.pepperpy.get_llm(
                provider="openai",
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            await self.llm.initialize()
            self.initialized = True
            self.logger.info("Initialized LLM test workflow")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM test workflow: {e}")
            raise WorkflowError("Failed to initialize LLM") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        try:
            if self.llm:
                await self.llm.cleanup()
            self.initialized = False
            self.logger.info("Cleaned up LLM test workflow")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute workflow.

        Args:
            input_data: Contains prompt and parameters

        Returns:
            Execution result with generated text
        """
        try:
            # Initialize if needed
            if not self.initialized:
                await self.initialize()

            # Get prompt from input
            prompt = input_data.get("prompt")
            if not prompt:
                raise WorkflowError("No prompt provided")

            # Get optional parameters
            system_prompt = input_data.get(
                "system_prompt", "You are a helpful AI assistant."
            )
            temperature = input_data.get("temperature", self.temperature)
            max_tokens = input_data.get("max_tokens", self.max_tokens)

            # Execute LLM call
            if not self.llm:
                raise WorkflowError("LLM not initialized")

            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "status": "success",
                "model": self.model,
                "prompt": prompt,
                "response": response,
                "metadata": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "system_prompt": system_prompt,
                },
            }

        except Exception as e:
            self.logger.error(f"Error executing LLM test: {e}")
            return {
                "status": "error",
                "message": str(e),
                "prompt": input_data.get("prompt"),
                "model": self.model,
            }
