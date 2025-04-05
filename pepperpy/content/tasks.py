"""
PepperPy Content Tasks.

Fluent API for content processing task configuration.
"""

from pathlib import Path
from typing import Any

from pepperpy.agent.task import TaskBase


class Processor(TaskBase):
    """Content processor configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize processor.

        Args:
            name: Processor name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["processor_type"] = name

    def prompt(self, text: str) -> "Processor":
        """Set the processor prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def input(self, content: Any) -> "Processor":
        """Set the input content.

        Args:
            content: Input content

        Returns:
            Self for method chaining
        """
        self._config["input"] = content
        return self

    def from_file(self, file_path: str | Path) -> "Processor":
        """Set input from a file.

        Args:
            file_path: Path to input file

        Returns:
            Self for method chaining
        """
        self._config["input_file"] = str(file_path)
        return self

    def parameters(self, params: dict[str, Any]) -> "Processor":
        """Set processing parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self

    def format(self, output_format: str) -> "Processor":
        """Set the output format.

        Args:
            output_format: Output format (json, text, markdown, etc.)

        Returns:
            Self for method chaining
        """
        self._config["format"] = output_format
        return self

    def output(self, path: str | Path) -> "Processor":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class DocumentProcessor(Processor):
    """Document processor configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize document processor.

        Args:
            name: Processor name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["document_type"] = None

    def document_type(self, doc_type: str) -> "DocumentProcessor":
        """Set the document type.

        Args:
            doc_type: Document type (pdf, docx, markdown, etc.)

        Returns:
            Self for method chaining
        """
        self._config["document_type"] = doc_type
        return self

    def extract_metadata(self, enable: bool = True) -> "DocumentProcessor":
        """Enable metadata extraction.

        Args:
            enable: Whether to extract metadata

        Returns:
            Self for method chaining
        """
        self._config["extract_metadata"] = enable
        return self


class ContentWorkflow(TaskBase):
    """Content processing workflow configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize content workflow.

        Args:
            name: Workflow name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._processors = []

    def add_processor(self, processor: Processor) -> "ContentWorkflow":
        """Add a processor to the workflow.

        Args:
            processor: Processor to add

        Returns:
            Self for method chaining
        """
        self._processors.append(processor)
        return self

    def output_dir(self, directory: str | Path) -> "ContentWorkflow":
        """Set the output directory for all results.

        Args:
            directory: Output directory path

        Returns:
            Self for method chaining
        """
        self._config["output_dir"] = str(directory)
        return self
