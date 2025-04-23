"""LLM test workflow provider implementation."""

from typing import dict, Any

from pepperpy import PepperPy
from pepperpy.core.base import PepperpyError
from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.workflow.base import WorkflowError

logger = logger.getLogger(__name__)


class WorkflowError(class WorkflowError(PepperpyError):
    """Base error for workflow errors."""):
    """
    Workflow workflowerror provider.
    
    This provider implements workflowerror functionality for the PepperPy workflow framework.
    """


class LLMTestWorkflow(...):
    model: str
    temperature: float
    max_tokens: int
    llm: Any
    pepperpy: Any
    pepperpy: Any
    pepperpy: Any
    pepperpy: Any
    llm: Any
    """Test workflow for LLM capabilities."""

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        await super().initialize()

        # Get configuration from self.config
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1000)

        # Initialize state
        self.llm = None
        self.pepperpy = None

        try:
            # Initialize LLM provider
            self.pepperpy = PepperPy()
            self.pepperpy = self.pepperpy.with_llm(
                provider="openai",
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            self.pepperpy = await self.pepperpy.build()

            # Get the LLM client
            self.llm = self.pepperpy.llm

            self.logger.debug(
                f"Initialized LLM test workflow with model={self.model}, "
                f"temperature={self.temperature}, max_tokens={self.max_tokens}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM test workflow: {e}")
            raise WorkflowError("Failed to initialize LLM") from e

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        try:
            if hasattr(self, "pepperpy") and self.pepperpy:
                await self.pepperpy.cleanup()
                self.pepperpy = None
                self.llm = None

            # Always call parent cleanup
            await super().cleanup()

            self.logger.debug("Cleaned up LLM test workflow")
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
            raise WorkflowError(f"Operation failed: {e}") from e
            self.logger.error(f"Error executing LLM test: {e}")
            return {
                "status": "error",
                "message": str(e),
                "prompt": input_data.get("prompt"),
                "model": self.model,
            }
