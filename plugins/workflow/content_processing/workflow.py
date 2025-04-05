"""
Content Processing Workflow

This workflow provides a comprehensive pipeline for processing textual content:
1. Text extraction from documents
2. Text normalization
3. Content generation
4. Content summarization
"""

import os
from typing import Any

from pepperpy.utils.logging import get_logger
from pepperpy.workflow.provider import WorkflowProvider


class ContentProcessingWorkflow(WorkflowProvider):
    """Content processing workflow for extraction, normalization, generation, and summarization."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the content processing workflow.

        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.output_dir = self.config.get("output_dir", "./output/content")
        self.auto_save_results = self.config.get("auto_save_results", True)
        self.log_level = self.config.get("log_level", "INFO")
        self.log_to_console = self.config.get("log_to_console", True)

        self.logger = get_logger(
            __name__, level=self.log_level, console=self.log_to_console
        )
        self.pepper: Any = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the pipeline and resources."""
        try:
            from pepperpy import PepperPy

            # Create output directory if it doesn't exist
            if self.auto_save_results:
                os.makedirs(self.output_dir, exist_ok=True)

            # Initialize PepperPy - using dynamic interface to avoid linter errors
            self.pepper = PepperPy()

            # Configure the pipeline with our settings
            # We're using a dynamic approach since we don't have strong typing for PepperPy
            try:
                # Try the fluent interface first (PepperPy().configure(...))
                configure_method = getattr(self.pepper, "configure", None)
                if callable(configure_method):
                    self.pepper = configure_method(
                        output_dir=self.output_dir,
                        log_level=self.log_level,
                        log_to_console=self.log_to_console,
                        auto_save_results=self.auto_save_results,
                    )
                else:
                    # Fall back to direct attribute setting
                    for attr, value in {
                        "output_dir": self.output_dir,
                        "log_level": self.log_level,
                        "log_to_console": self.log_to_console,
                        "auto_save_results": self.auto_save_results,
                    }.items():
                        if hasattr(self.pepper, attr):
                            setattr(self.pepper, attr, value)
            except Exception as e:
                self.logger.warning(f"Error configuring PepperPy: {e}")

            self.initialized = True
            self.logger.info("Content processing workflow initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize content processing workflow: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.pepper = None
        self.initialized = False
        self.logger.info("Content processing workflow cleaned up")

    def _create_workflow(self, task_input: dict[str, Any]) -> list[Any]:
        """Create a workflow configuration based on input parameters.

        Args:
            task_input: Input parameters for the workflow

        Returns:
            List of processor configurations
        """
        if not self.initialized or not self.pepper:
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
            processors: List of configured processors

        Returns:
            Dictionary of processing results
        """
        if not self.initialized or not self.pepper:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")

        try:
            # Execute all processors
            run_processors = getattr(self.pepper, "run_processors", None)
            if not callable(run_processors):
                raise RuntimeError(
                    "PepperPy instance does not have a 'run_processors' method"
                )

            await run_processors(processors)

            # Collect results
            results = {}
            for processor in processors:
                # Get processor type and output path
                processor_type = getattr(processor, "name", "unknown")
                output_path = getattr(processor, "output_path", None)

                # If output was saved to file and auto_save_results is enabled
                if output_path and self.auto_save_results:
                    try:
                        with open(output_path) as f:
                            results[processor_type] = f.read()
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to read output file {output_path}: {e}"
                        )
                        results[processor_type] = f"Error reading output: {e!s}"
                else:
                    # If no output file or auto_save not enabled, use processor result
                    results[processor_type] = getattr(
                        processor, "result", "No result available"
                    )

            return {"results": results, "success": True}
        except Exception as e:
            self.logger.error(f"Error processing content: {e}")
            return {"error": str(e), "success": False}

    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute the content processing workflow.

        Args:
            data: Input data for the workflow with task and parameters

        Returns:
            Results of the workflow execution
        """
        try:
            # Make sure workflow is initialized
            if not self.initialized:
                await self.initialize()

            task = data.get("task", "")
            if task != "process_content":
                return {"error": f"Unsupported task: {task}", "success": False}

            # Get input parameters
            input_data = data.get("input", {})
            if not input_data:
                return {"error": "No input data provided", "success": False}

            # Create and execute workflow
            processors = self._create_workflow(input_data)
            if not processors:
                return {"error": "No processors configured", "success": False}

            return await self._process_content(processors)
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            return {"error": str(e), "success": False}
        finally:
            # Cleanup resources
            await self.cleanup()
