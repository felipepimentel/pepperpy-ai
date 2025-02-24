"""Unified content processor system for handling different types of content."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

from pepperpy.core.errors.unified import PepperpyError
from pepperpy.core.metrics.unified import MetricsManager

T = TypeVar("T")
R = TypeVar("R")


class ProcessorError(PepperpyError):
    """Base error class for processor-related errors."""

    def __init__(self, message: str, code: str = "PROC001", **kwargs: Any) -> None:
        """Initialize the error."""
        super().__init__(message, code=code, category="processor", **kwargs)


@dataclass
class ProcessingContext:
    """Context for content processing."""

    content_type: str
    metadata: dict[str, Any]
    options: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "content_type": self.content_type,
            "metadata": self.metadata,
            "options": self.options,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ProcessingResult(Generic[R]):
    """Result of content processing."""

    content: R
    metadata: dict[str, Any]
    errors: list[str]
    warnings: list[str]
    processing_time: float

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time": self.processing_time,
        }


class ContentProcessor(ABC, Generic[T, R]):
    """Base class for content processors."""

    @abstractmethod
    async def process(
        self, content: T, context: ProcessingContext
    ) -> ProcessingResult[R]:
        """Process content."""
        pass

    @abstractmethod
    async def validate(self, content: T, context: ProcessingContext) -> list[str]:
        """Validate content."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class ProcessorRegistry:
    """Registry for content processors."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._processors: dict[str, dict[str, ContentProcessor]] = {}
        self._metrics = MetricsManager.get_instance()

    def register(
        self, content_type: str, version: str, processor: ContentProcessor
    ) -> None:
        """Register a content processor.

        Args:
            content_type: Type of content the processor handles.
            version: Version of the processor.
            processor: The processor instance.

        Raises:
            ProcessorError: If processor already exists.
        """
        if content_type not in self._processors:
            self._processors[content_type] = {}

        if version in self._processors[content_type]:
            raise ProcessorError(
                f"Processor already exists: {content_type} {version}",
                code="PROC002",
            )

        self._processors[content_type][version] = processor
        self._metrics.counter(
            "processor_registrations",
            1,
            content_type=content_type,
            version=version,
        )

    async def get_processor(
        self, content_type: str, version: str | None = None
    ) -> ContentProcessor:
        """Get content processor.

        Args:
            content_type: Type of content to process.
            version: Optional version of the processor.

        Returns:
            The requested processor.

        Raises:
            ProcessorError: If processor not found.
        """
        if content_type not in self._processors:
            raise ProcessorError(
                f"Processor not found: {content_type}",
                code="PROC003",
            )

        processors = self._processors[content_type]
        if not version:
            # Get latest version
            version = max(processors.keys())

        if version not in processors:
            raise ProcessorError(
                f"Version not found: {version}",
                code="PROC004",
            )

        return processors[version]


class TextProcessor(ContentProcessor[str, str]):
    """Process text content."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the processor.

        Args:
            config: Configuration options.
        """
        self.config = config
        self._metrics = MetricsManager.get_instance()

    async def process(
        self, content: str, context: ProcessingContext
    ) -> ProcessingResult[str]:
        """Process text content.

        Args:
            content: Text content to process.
            context: Processing context.

        Returns:
            Processing result.
        """
        start_time = time.time()

        try:
            # Process text content
            processed = self._process_text(content, context)

            return ProcessingResult(
                content=processed,
                metadata={"config": self.config},
                errors=[],
                warnings=[],
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            return ProcessingResult(
                content=content,
                metadata={"error": str(e)},
                errors=[str(e)],
                warnings=[],
                processing_time=time.time() - start_time,
            )

    async def validate(self, content: str, context: ProcessingContext) -> list[str]:
        """Validate text content.

        Args:
            content: Text content to validate.
            context: Processing context.

        Returns:
            List of validation errors.
        """
        errors = []

        if not content:
            errors.append("Empty content")

        if len(content) > self.config.get("max_length", 1000000):
            errors.append("Content too long")

        return errors

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    def _process_text(self, content: str, context: ProcessingContext) -> str:
        """Process text content.

        Args:
            content: Text content to process.
            context: Processing context.

        Returns:
            Processed text content.
        """
        # Apply text processing based on context options
        processed = content

        if context.options.get("normalize", False):
            processed = processed.strip().lower()

        if context.options.get("remove_whitespace", False):
            processed = " ".join(processed.split())

        return processed


class CodeProcessor(ContentProcessor[str, str]):
    """Process code content."""

    def __init__(self, language: str) -> None:
        """Initialize the processor.

        Args:
            language: Programming language.
        """
        self.language = language
        self._metrics = MetricsManager.get_instance()

    async def process(
        self, content: str, context: ProcessingContext
    ) -> ProcessingResult[str]:
        """Process code content.

        Args:
            content: Code content to process.
            context: Processing context.

        Returns:
            Processing result.
        """
        start_time = time.time()

        try:
            # Process code content
            processed = self._process_code(content, context)

            return ProcessingResult(
                content=processed,
                metadata={"language": self.language},
                errors=[],
                warnings=[],
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            return ProcessingResult(
                content=content,
                metadata={"error": str(e)},
                errors=[str(e)],
                warnings=[],
                processing_time=time.time() - start_time,
            )

    async def validate(self, content: str, context: ProcessingContext) -> list[str]:
        """Validate code content.

        Args:
            content: Code content to validate.
            context: Processing context.

        Returns:
            List of validation errors.
        """
        errors = []

        if not content:
            errors.append("Empty content")

        if not self._is_valid_syntax(content):
            errors.append(f"Invalid {self.language} syntax")

        return errors

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    def _process_code(self, content: str, context: ProcessingContext) -> str:
        """Process code content.

        Args:
            content: Code content to process.
            context: Processing context.

        Returns:
            Processed code content.
        """
        # Apply code processing based on context options
        processed = content

        if context.options.get("format", False):
            processed = self._format_code(processed)

        if context.options.get("remove_comments", False):
            processed = self._remove_comments(processed)

        return processed

    def _is_valid_syntax(self, content: str) -> bool:
        """Check if code has valid syntax.

        Args:
            content: Code content to check.

        Returns:
            True if syntax is valid, False otherwise.
        """
        try:
            if self.language == "python":
                compile(content, "<string>", "exec")
            return True
        except SyntaxError:
            return False

    def _format_code(self, content: str) -> str:
        """Format code content.

        Args:
            content: Code content to format.

        Returns:
            Formatted code content.
        """
        # Implement language-specific formatting
        return content

    def _remove_comments(self, content: str) -> str:
        """Remove comments from code.

        Args:
            content: Code content to process.

        Returns:
            Code content without comments.
        """
        # Implement language-specific comment removal
        return content


class ProcessorMonitor:
    """Monitor for content processors."""

    def __init__(self) -> None:
        """Initialize the monitor."""
        self._metrics = MetricsManager.get_instance()

    async def record_processing(
        self,
        processor: str,
        content_type: str,
        success: bool = True,
        processing_time: float = 0.0,
        **labels: str,
    ) -> None:
        """Record processing operation.

        Args:
            processor: Name of the processor.
            content_type: Type of content processed.
            success: Whether processing was successful.
            processing_time: Time taken to process.
            **labels: Additional metric labels.
        """
        self._metrics.counter(
            "processor_operations",
            1,
            processor=processor,
            content_type=content_type,
            success=str(success).lower(),
            **labels,
        )

        self._metrics.histogram(
            "processor_time",
            processing_time,
            processor=processor,
            content_type=content_type,
            **labels,
        )
