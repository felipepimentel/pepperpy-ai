"""Base classes for the PepperPy pipeline framework.

This module defines the core classes that make up the pipeline framework:
- Pipeline: The main container for a sequence of operations
- PipelineStage: The base class for all pipeline stages
- PipelineContext: Context for passing data and metadata between stages
- PipelineConfig: Configuration for pipelines
- PipelineRegistry: Registry for storing and retrieving pipelines
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar, cast

# Importe a classe de erro do módulo correto com a grafia correta
from pepperpy.core import PepperpyError

# Type variables for generic pipeline stages
Input = TypeVar("Input")
Output = TypeVar("Output")
T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger(__name__)


class PipelineError(PepperpyError):
    """Error raised by pipeline operations."""

    pass


@dataclass
class PipelineContext:
    """Context for pipeline execution.

    This class stores data and metadata that is passed between pipeline stages.
    It provides a way to share state throughout the pipeline execution.
    """

    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context data.

        Args:
            key: The key to get
            default: Default value if key is not found

        Returns:
            The value associated with the key or the default
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context data.

        Args:
            key: The key to set
            value: The value to set
        """
        self.data[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value.

        Args:
            key: The key to get
            default: Default value if key is not found

        Returns:
            The metadata value associated with the key or the default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value.

        Args:
            key: The key to set
            value: The value to set
        """
        self.metadata[key] = value


@dataclass
class PipelineConfig:
    """Configuration for a pipeline.

    This class stores configuration options for a pipeline.
    """

    name: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)


class PipelineStage(Generic[Input, Output], ABC):
    """Base class for all pipeline stages.

    A pipeline stage is a unit of work that takes an input and produces an output.
    Pipeline stages can be chained together to form a pipeline.
    """

    def __init__(self, name: str, description: str = ""):
        """Initialize a pipeline stage.

        Args:
            name: The name of the stage
            description: A description of the stage
        """
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        """Get the name of the stage.

        Returns:
            The name of the stage
        """
        return self._name

    @property
    def description(self) -> str:
        """Get the description of the stage.

        Returns:
            The description of the stage
        """
        return self._description

    @abstractmethod
    def process(self, input_data: Input, context: PipelineContext) -> Output:
        """Process the input data and return the output.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            The processed output data

        Raises:
            PipelineError: If an error occurs during processing
        """
        pass

    def __call__(
        self, input_data: Input, context: Optional[PipelineContext] = None
    ) -> Output:
        """Call the stage's process method.

        Args:
            input_data: The input data to process
            context: The pipeline context, created if None

        Returns:
            The processed output data
        """
        if context is None:
            context = PipelineContext()

        try:
            logger.debug(f"Executing pipeline stage: {self.name}")
            return self.process(input_data, context)
        except Exception as e:
            logger.error(f"Error in pipeline stage {self.name}: {str(e)}")
            raise PipelineError(f"Error in pipeline stage {self.name}: {str(e)}") from e


class Pipeline(Generic[Input, Output]):
    """A pipeline that processes data through a sequence of stages.

    A pipeline is composed of a series of stages that are executed in sequence.
    Each stage takes the output of the previous stage as input.
    """

    def __init__(
        self,
        name: str,
        stages: Optional[List[PipelineStage]] = None,
        config: Optional[PipelineConfig] = None,
    ):
        """Initialize a pipeline.

        Args:
            name: The name of the pipeline
            stages: The stages of the pipeline (optional)
            config: Configuration for the pipeline (optional)
        """
        self._name = name
        self._stages = stages if stages is not None else []
        self._config = config or PipelineConfig(name=name)

    @property
    def name(self) -> str:
        """Get the name of the pipeline.

        Returns:
            The name of the pipeline
        """
        return self._name

    @property
    def stages(self) -> List[PipelineStage]:
        """Get the stages of the pipeline.

        Returns:
            The pipeline stages
        """
        return self._stages

    @property
    def config(self) -> PipelineConfig:
        """Get the pipeline configuration.

        Returns:
            The pipeline configuration
        """
        return self._config

    def add_stage(self, stage: PipelineStage) -> "Pipeline":
        """Add a stage to the pipeline.

        Args:
            stage: The stage to add

        Returns:
            The pipeline instance for chaining
        """
        self._stages.append(stage)
        return self

    def execute(
        self, input_data: Input, context: Optional[PipelineContext] = None
    ) -> Output:
        """Execute the pipeline on the input data.

        Args:
            input_data: The input data to process
            context: The pipeline context, created if None

        Returns:
            The processed output data

        Raises:
            PipelineError: If an error occurs during execution
        """
        if context is None:
            context = PipelineContext()

        # Store the pipeline name in the context
        context.set_metadata("pipeline_name", self.name)

        # Special case: empty pipeline
        if not self._stages:
            logger.warning(f"Pipeline {self.name} has no stages")
            return cast(Output, input_data)

        try:
            logger.info(f"Starting pipeline: {self.name}")
            current_data = input_data

            # Process each stage in sequence
            for i, stage in enumerate(self._stages):
                logger.debug(
                    f"Pipeline {self.name}: executing stage {i + 1}/{len(self._stages)}: {stage.name}"
                )
                context.set_metadata("current_stage", stage.name)
                context.set_metadata("stage_index", i)
                current_data = stage(current_data, context)

            logger.info(f"Pipeline {self.name} completed successfully")
            return cast(Output, current_data)

        except Exception as e:
            logger.error(f"Error in pipeline {self.name}: {str(e)}")
            raise PipelineError(f"Error in pipeline {self.name}: {str(e)}") from e


class PipelineRegistry:
    """Registry for storing and retrieving pipelines.

    This class provides a central registry for pipelines, allowing them to be
    stored and retrieved by name.
    """

    _instance = None

    def __new__(cls):
        """Create a new instance or return the existing one."""
        if cls._instance is None:
            cls._instance = super(PipelineRegistry, cls).__new__(cls)
            cls._instance._pipelines = {}
        return cls._instance

    def __init__(self):
        """Initialize the registry."""
        # Inicializa o dicionário se ainda não estiver definido
        if not hasattr(self, "_pipelines"):
            self._pipelines = {}

    def register(self, pipeline: Pipeline) -> None:
        """Register a pipeline.

        Args:
            pipeline: The pipeline to register

        Raises:
            ValueError: If a pipeline with the same name already exists
        """
        if pipeline.name in self._pipelines:
            raise ValueError(f"Pipeline with name '{pipeline.name}' already registered")

        self._pipelines[pipeline.name] = pipeline
        logger.debug(f"Registered pipeline: {pipeline.name}")

    def unregister(self, name: str) -> None:
        """Unregister a pipeline.

        Args:
            name: The name of the pipeline to unregister

        Raises:
            KeyError: If no pipeline with the given name exists
        """
        if name not in self._pipelines:
            raise KeyError(f"No pipeline registered with name '{name}'")

        del self._pipelines[name]
        logger.debug(f"Unregistered pipeline: {name}")

    def get(self, name: str) -> Pipeline:
        """Get a pipeline by name.

        Args:
            name: The name of the pipeline to get

        Returns:
            The pipeline with the given name

        Raises:
            KeyError: If no pipeline with the given name exists
        """
        if name not in self._pipelines:
            raise KeyError(f"No pipeline registered with name '{name}'")

        return self._pipelines[name]

    def list(self) -> List[str]:
        """List all registered pipeline names.

        Returns:
            A list of registered pipeline names
        """
        return list(self._pipelines.keys())

    def clear(self) -> None:
        """Clear all registered pipelines."""
        self._pipelines.clear()
        logger.debug("Cleared all registered pipelines")


# Global functions for working with the pipeline registry

_registry = PipelineRegistry()


def get_registry() -> PipelineRegistry:
    """Get the global pipeline registry.

    Returns:
        The global pipeline registry
    """
    return _registry


def register_pipeline(pipeline: Pipeline) -> None:
    """Register a pipeline in the global registry.

    Args:
        pipeline: The pipeline to register
    """
    _registry.register(pipeline)


def get_pipeline(name: str) -> Pipeline:
    """Get a pipeline from the global registry.

    Args:
        name: The name of the pipeline to get

    Returns:
        The pipeline with the given name
    """
    return _registry.get(name)


def create_pipeline(
    name: str, stages: Optional[List[PipelineStage]] = None
) -> Pipeline:
    """Create a new pipeline and register it.

    Args:
        name: The name of the pipeline
        stages: The stages of the pipeline (optional)

    Returns:
        The created pipeline
    """
    pipeline = Pipeline(name=name, stages=stages)
    register_pipeline(pipeline)
    return pipeline


def execute_pipeline(
    name: str, input_data: Any, context: Optional[PipelineContext] = None
) -> Any:
    """Execute a pipeline from the global registry.

    Args:
        name: The name of the pipeline to execute
        input_data: The input data for the pipeline
        context: The pipeline context (optional)

    Returns:
        The output from the pipeline
    """
    pipeline = get_pipeline(name)
    return pipeline.execute(input_data, context)


class Workflow(ABC):
    """Base class for all workflows.

    A workflow is a high-level abstraction that combines multiple components
    to achieve a specific goal. Workflows are responsible for:
    - Component orchestration
    - State management
    - Error handling
    - Progress tracking
    """

    @abstractmethod
    def __init__(self) -> None:
        """Initialize workflow."""
        pass
