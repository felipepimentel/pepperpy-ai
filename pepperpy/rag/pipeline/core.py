"""Core pipeline components for the RAG system.

This module provides the core abstractions and base classes for the RAG pipeline,
including configuration management and pipeline stages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pepperpy.errors import PepperpyError
from pepperpy.rag.document.core import DocumentChunk

# Type variables for generic pipeline components
Input = TypeVar("Input")
Output = TypeVar("Output")

# Pipeline specific types
PipelineInput = Union[str, Dict[str, Any]]
PipelineOutput = Union[str, List[DocumentChunk], Dict[str, Any]]
PipelineStep = Union[str, Dict[str, Any]]


@dataclass
class PipelineConfig:
    """Base configuration for pipeline components."""

    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class PipelineStage(Generic[Input, Output], ABC):
    """Base class for pipeline stages.

    A pipeline stage represents a single step in the processing pipeline that
    transforms input data into output data.
    """

    def __init__(self, config: PipelineConfig):
        """Initialize the stage.

        Args:
            config: Stage configuration
        """
        self.config = config

    @abstractmethod
    async def process(
        self,
        input_data: Input,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Output:
        """Process input data to produce output.

        Args:
            input_data: Input data to process
            metadata: Optional metadata

        Returns:
            Processed output

        Raises:
            PepperpyError: If processing fails
        """
        pass


class Pipeline(Generic[Input, Output]):
    """Base class for pipelines.

    A pipeline is a sequence of stages that process data in order.
    """

    def __init__(self, config: PipelineConfig):
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> "Pipeline":
        """Add a stage to the pipeline.

        Args:
            stage: Stage to add

        Returns:
            Self for chaining
        """
        self.stages.append(stage)
        return self

    async def process(
        self,
        input_data: Input,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Output:
        """Process input data through all stages.

        Args:
            input_data: Input data to process
            metadata: Optional metadata

        Returns:
            Final output

        Raises:
            PepperpyError: If processing fails
        """
        try:
            current_data = input_data
            for stage in self.stages:
                current_data = await stage.process(current_data, metadata)
            return current_data  # type: ignore
        except Exception as e:
            raise PepperpyError(f"Error in pipeline processing: {e}")


# Export all classes and types
__all__ = [
    # Types
    "PipelineInput",
    "PipelineOutput",
    "PipelineStep",
    # Classes
    "PipelineConfig",
    "PipelineStage",
    "Pipeline",
]
