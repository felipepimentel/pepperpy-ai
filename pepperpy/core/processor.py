"""@file: processor.py
@purpose: Core processor base class for the Pepperpy framework
@component: Core
@created: 2024-02-18
@updated: 2024-03-21
@task: TASK-007-R060
@status: active
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar

from .processors import (
    ContentProcessor,
    ProcessingContext,
    ProcessingResult,
    ProcessorRegistry,
)

T = TypeVar("T")


class Processor(ABC, Generic[T]):
    """Base class for all processors in the framework.

    Processors are responsible for transforming data from one form to another.
    They can be used for pre-processing inputs, post-processing outputs,
    or any other data transformation needs.

    This class has been enhanced to support the new content processing system
    introduced in TASK-007-R060. For content-specific processing, use the
    ContentProcessor class from the processors module.
    """

    def __init__(self):
        self._processor_registry = ProcessorRegistry.get_instance()

    @abstractmethod
    async def process(self, data: T, **kwargs: Any) -> T:
        """Process the input data.

        Args:
            data: Input data to process
            **kwargs: Additional processing parameters

        Returns:
            Processed data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError

    async def get_content_processor(
        self,
        content_type: str,
        version: str | None = None
    ) -> ContentProcessor:
        """Get a content processor from the registry.

        Args:
            content_type: Type of content to process
            version: Optional version of the processor

        Returns:
            Content processor instance
        """
        return await self._processor_registry.get_processor(content_type, version)

    async def process_content(
        self,
        content: Any,
        content_type: str,
        metadata: Dict[str, Any] | None = None,
        options: Dict[str, Any] | None = None,
        version: str | None = None,
    ) -> ProcessingResult:
        """Process content using a registered content processor.

        Args:
            content: Content to process
            content_type: Type of content
            metadata: Optional metadata
            options: Optional processing options
            version: Optional processor version

        Returns:
            Processing result
        """
        processor = await self.get_content_processor(content_type, version)
        context = ProcessingContext(
            content_type=content_type,
            metadata=metadata or {},
            options=options or {},
        )
        return await processor.process(content, context)
