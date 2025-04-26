"""
LLM Completion Workflow

A simple workflow for generating text with Large Language Models:
1. Text completion with various prompts
2. Content generation with custom system instructions
3. Completion with basic formatting options
"""

import os
from pathlib import Path
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.workflow.base import WorkflowProvider


class LLMCompletionWorkflow(WorkflowProvider):
    """Simple workflow for LLM completions and text generation."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the LLM completion workflow.

        Args:
            config: Configuration parameters
        """
        self.config = config or {}

        # LLM configuration
        self.provider = self.config.get("provider", "openai")
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.api_key = self.config.get(
            "api_key", os.environ.get(f"{self.provider.upper()}_API_KEY", "")
        )
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.system_prompt = self.config.get(
            "system_prompt",
            "You are a helpful assistant powered by the PepperPy framework.",
        )

        # Output configuration
        self.output_dir = self.config.get("output_dir", "./output/llm")

        # Logging
        self.log_level = self.config.get("log_level", "INFO")
        self.log_to_console = self.config.get("log_to_console", True)
        self.logger = get_logger(__name__)

        # State
        self.pepperpy = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize LLM provider and resources."""
        if self.initialized:
            return

        try:
            # Import PepperPy main class
            from pepperpy.pepperpy import PepperPy

            # Create output directory if needed
            os.makedirs(self.output_dir, exist_ok=True)

            # Initialize PepperPy with default LLM provider from config
            self.pepperpy = PepperPy()
            
            # Set up the LLM provider using OpenRouter (definido como padrão no config.yaml)
            self.pepperpy.with_llm("openrouter")

            # Initialize the instance
            await self.pepperpy.initialize()
            
            self.initialized = True
            self.logger.info("Initialized LLM completion workflow with OpenRouter")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM workflow: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        try:
            if self.pepperpy:
                await self.pepperpy.cleanup()
                self.pepperpy = None
                
            self.initialized = False
            self.logger.info("Cleaned up LLM completion workflow resources")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise

    async def _complete(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Generate a completion.

        Args:
            input_data: Input data containing prompt and options

        Returns:
            Dict containing the generated text
        """
        if not self.initialized or not self.pepperpy:
            await self.initialize()
            if not self.initialized or not self.pepperpy:
                return {"error": "Failed to initialize LLM provider", "success": False}

        # Extract parameters from input
        prompt = input_data.get("prompt", "")
        if not prompt:
            return {"error": "No prompt provided", "success": False}

        # Get system prompt (override if provided in input)
        system_prompt = input_data.get("system_prompt", self.system_prompt)

        # Get other options
        temperature = input_data.get("temperature", self.temperature)
        max_tokens = input_data.get("max_tokens", self.max_tokens)

        # Additional options
        options = input_data.get("options", {})
        options.update({"temperature": temperature, "max_tokens": max_tokens})

        try:
            # Make sure we can access the LLM provider
            if not hasattr(self.pepperpy, "llm"):
                return {
                    "error": "LLM provider not properly initialized",
                    "success": False,
                }

            # For chat models, we format as a chat
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            # Check if the llm attribute has the chat method
            if not hasattr(self.pepperpy.llm, "chat"):
                return {
                    "error": "LLM provider does not support chat completions",
                    "success": False,
                }

            # Call LLM provider for chat
            result = await self.pepperpy.llm.chat(messages, **options)

            # Save result to file if requested
            output_file = input_data.get("output_file", "")
            if output_file and self.output_dir:
                file_path = Path(self.output_dir) / output_file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(result)
                self.logger.info(f"Saved completion to {file_path}")

            return {
                "text": result,
                "success": True,
                "prompt": prompt,
                "model": self.model,
                "provider": self.provider,
            }
        except Exception as e:
            self.logger.error(f"Text completion error: {e}")
            return {"error": str(e), "success": False}

    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute the LLM completion workflow.

        Args:
            data: Input data with task and parameters

        Returns:
            Results of the workflow execution
        """
        try:
            # Initialize if not already initialized
            if not self.initialized:
                await self.initialize()

            # Get task and input
            task = data.get("task", "complete")
            input_data = data.get("input", {})

            # Handle different tasks
            if task == "complete":
                return await self._complete(input_data)
            else:
                return {"error": f"Unsupported task: {task}", "success": False}
        except Exception as e:
            self.logger.error(f"Workflow execution error: {e}")
            return {"error": str(e), "success": False}
        finally:
            # We don't cleanup after each execution to allow for
            # reuse of the LLM provider
            pass
