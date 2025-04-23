"""
Content Processing Workflow Provider.

This workflow provides a comprehensive pipeline for processing textual content:
1. Text extraction from documents
2. Text normalization
3. Content generation
4. Content summarization
"""

import importlib
import os
from typing import dict, list, Optional, Any

from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.workflow.base import WorkflowError

logger = logger.getLogger(__name__)


class ContentProcessingProvider(class ContentProcessingProvider(WorkflowProvider, ProviderPlugin):
    """Content processing workflow provider for extraction, normalization, generation, and summarization.

    This workflow makes it easy to process content through multiple stages,
    with configurable processors and parameters.

    Features:
    - Text Extraction: Extract key information from documents
    - Text Normalization: Normalize text with consistent terminology and formatting
    - Content Generation: Generate new content based on input and prompts
    - Content Summarization: Create concise summaries of longer documents
    """):
    """
    Workflow contentprocessing provider.
    
    This provider implements contentprocessing functionality for the PepperPy workflow framework.
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        # Call parent initialize first
        await super().initialize()

        if self.initialized:
            return

        try:
            # Get configuration
            self.output_dir = self.config.get("output_dir", "./output/content")
            self.auto_save_results = self.config.get("auto_save_results", True)

            # Create output directory if it doesn't exist
            if self.auto_save_results:
                os.makedirs(self.output_dir, exist_ok=True)

            # Use importlib to avoid circular imports
            pepperpy_module = importlib.import_module("pepperpy")

            # Get the PepperPy class
            PepperPy = getattr(pepperpy_module, "PepperPy", None)
            if not PepperPy:
                raise ImportError("Could not import PepperPy class")

            # Create PepperPy instance
            self.pepper = PepperPy.create()

            # Configure based on workflow settings
            if self.auto_save_results:
                self.pepper.with_output_dir(self.output_dir)

            # Build the configured instance
            self.pepper = self.pepper.build()

            self.logger.info("Content processing workflow initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize content processing workflow: {e}")
            # Make sure to clean up any partial initialization
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        try:
            # Release resources
            self.pepper = None
            self.logger.info("Content processing workflow resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error during content processing workflow cleanup: {e}")

        # Always call parent cleanup last
        await super().cleanup()

    def _create_workflow(self, task_input: dict[str, Any]) -> list[Any]:
        """Create a workflow configuration based on input parameters.

        Args:
            task_input: Input parameters for the workflow

        Returns:
            list of processor configurations
        """
        if not self.initialized or not hasattr(self, "pepper") or not self.pepper:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")

        content = task_input.get("content", "")
        processors = task_input.get("processors", [])

        # If no processors specified, use defaults
        if not processors:
            processors = [
                {
                    "type": "text_extraction",
                    "prompt": "Extract key information and concepts from this content.",
                    "output": "extraction_result.txt",
                },
                {
                    "type": "text_normalization",
                    "prompt": "Normalize this text with consistent terminology and formatting.",
                    "output": "normalization_result.txt",
                },
                {
                    "type": "content_summarization",
                    "prompt": "Provide a concise summary of this content.",
                    "parameters": {"sentences": 3, "style": "concise"},
                    "output": "summarization_result.txt",
                },
            ]

        # Create processor configurations
        configured_processors = []

        # Get the processor method
        processor_method = getattr(self.pepper, "processor", None)
        if not callable(processor_method):
            raise RuntimeError("PepperPy instance does not have a 'processor' method")

        for proc in processors:
            processor_type = proc.get("type")
            if not processor_type:
                continue

            # Create processor
            processor = processor_method(processor_type)

            # Configure processor
            if "prompt" in proc and hasattr(processor, "prompt"):
                processor.prompt(proc["prompt"])

            if hasattr(processor, "input"):
                if "input" in proc:
                    processor.input(proc["input"])
                elif content:
                    processor.input(content)

            if "parameters" in proc and hasattr(processor, "parameters"):
                processor.parameters(proc["parameters"])

            if "output" in proc and hasattr(processor, "output"):
                processor.output(proc["output"])

            configured_processors.append(processor)

        return configured_processors

    async def _process_content(self, processors: list[Any]) -> dict[str, Any]:
        """Process content through the configured processors.

        Args:
            processors: list of configured processors

        Returns:
            Dictionary of processing results
        """
        if not self.initialized or not hasattr(self, "pepper") or not self.pepper:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")

        try:
            # Execute all processors
            results = {}

            for processor in processors:
                try:
                    # Execute the processor
                    processor_type = getattr(processor, "name", "unknown")
                    self.logger.info(f"Executing processor: {processor_type}")

                    # Use the real execute method
                    result = await processor.execute()

                    # Store the result
                    results[processor_type] = result

                    self.logger.info(
                        f"Processor {processor_type} completed successfully"
                    )
                except Exception as e:
                    raise WorkflowError(f"Operation failed: {e}") from e
                    self.logger.error(
                        f"Error executing processor {processor_type}: {e}"
                    )
                    results[processor_type] = {"error": str(e)}

            return results
        except Exception as e:
            self.logger.error(f"Error processing content: {e}")
            raise

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the content processing workflow.

        Args:
            input_data: Input data for the workflow with task and parameters:
                {
                    "task": str,  # Task name (default: "process_content")
                    "input": {    # Content and processor configurations
                        "content": str,  # Text content to process
                        "processors": [  # list of processor configurations
                            {
                                "type": str,  # Processor type
                                "prompt": str,  # Processing prompt
                                "parameters": dict,  # Optional parameters
                                "output": str  # Output file name
                            }
                        ]
                    }
                }

        Returns:
            Results of the workflow execution:
            {
                "status": str,  # "success" or "error"
                "message": str,  # Human readable message
                "results": {     # Results by processor type
                    "processor_type": Any  # Output from each processor
                }
            }
        """
        # Make sure workflow is initialized
        if not self.initialized:
            await self.initialize()

        try:
            # Get task type from input
            task = input_data.get("task", "process_content")
            self.logger.info(f"Executing task: {task}")

            if task != "process_content":
                raise WorkflowError(f"Unsupported task: {task)"}

            # Get input parameters
            task_input = input_data.get("input", {})
            if not task_input and "content" in input_data:
                # Allow content to be passed directly
                task_input = {"content": input_data.get("content", "")}
                self.logger.debug(
                    f"Using content directly from input_data: {task_input}"
                )

            if not task_input:
                raise WorkflowError("No input content provided")

            # Create and execute workflow
            processors = self._create_workflow(task_input)
            if not processors:
                raise WorkflowError("No processors configured")

            # Process the content
            results = await self._process_content(processors)

            # Return results
            return {
                "status": "success",
                "message": "Content processing completed successfully",
                "results": results,
            }

        except Exception as e:
            self.logger.error(f"Error executing content processing workflow: {e}")
            return {"status": "error", "message": str(e)}
