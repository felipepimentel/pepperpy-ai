"""Base classes for the PepperPy pipeline framework.

This module defines the core classes that make up the pipeline framework:
- Pipeline: The main container for a sequence of operations
- PipelineStage: The base class for all pipeline stages
- PipelineContext: Context for passing data and metadata between stages
- PipelineConfig: Configuration for pipelines
- PipelineRegistry: Registry for storing and retrieving pipelines
"""

import enum
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, TypeVar, cast

# Import from the correct module structure
from pepperpy.core import PepperpyError
from pepperpy.core.errors import ValidationError
from pepperpy.plugin import PepperpyPlugin, create_provider_instance

# Type variables for generic pipeline stages
Input = TypeVar("Input")
Output = TypeVar("Output")
T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger(__name__)

__all__ = [
    "ComponentType",
    "DocumentWorkflow",
    "Pipeline",
    "PipelineConfig",
    "PipelineContext",
    "PipelineError",
    "PipelineRegistry",
    "PipelineStage",
    "Workflow",
    "WorkflowComponent",
    "WorkflowProvider",
    "create_provider",
]


class ComponentType(str, enum.Enum):
    """Type of workflow component."""

    SOURCE = "source"
    PROCESSOR = "processor"
    SINK = "sink"
    AGENT = "agent"
    TRIGGER = "trigger"
    ACTION = "action"


class PipelineError(PepperpyError):
    """Error raised by pipeline operations."""

    pass


@dataclass
class PipelineContext:
    """Context for pipeline execution.

    This class stores data and metadata that is passed between pipeline stages.
    It provides a way to share state throughout the pipeline execution.
    """

    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

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
    metadata: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


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
        self, input_data: Input, context: PipelineContext | None = None
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
            logger.error(f"Error in pipeline stage {self.name}: {e!s}")
            raise PipelineError(f"Error in pipeline stage {self.name}: {e!s}") from e


class Pipeline(Generic[Input, Output]):
    """A pipeline that processes data through a sequence of stages.

    A pipeline is composed of a series of stages that are executed in sequence.
    Each stage takes the output of the previous stage as input.
    """

    def __init__(
        self,
        name: str,
        stages: list[PipelineStage] | None = None,
        config: PipelineConfig | None = None,
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
    def stages(self) -> list[PipelineStage]:
        """Get the stages of the pipeline.

        Returns:
            The stages of the pipeline
        """
        return self._stages

    @property
    def config(self) -> PipelineConfig:
        """Get the pipeline configuration.

        Returns:
            The pipeline configuration
        """
        return self._config

    def add_stage(self, stage: PipelineStage) -> None:
        """Add a stage to the pipeline.

        Args:
            stage: The stage to add
        """
        self._stages.append(stage)

    def process(
        self, input_data: Input, context: PipelineContext | None = None
    ) -> Output:
        """Process data through the pipeline.

        Args:
            input_data: The input data to process
            context: The pipeline context, created if None

        Returns:
            The processed output data

        Raises:
            PipelineError: If an error occurs during processing
        """
        if context is None:
            context = PipelineContext()

        try:
            logger.debug(f"Executing pipeline: {self.name}")
            data = input_data
            for stage in self._stages:
                data = stage(data, context)
            return cast(Output, data)
        except Exception as e:
            logger.error(f"Error in pipeline {self.name}: {e!s}")
            raise PipelineError(f"Error in pipeline {self.name}: {e!s}") from e


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

    def list(self) -> list[str]:
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


def get_pipeline_registry() -> PipelineRegistry:
    """Get the global pipeline registry.

    Returns:
        The global pipeline registry
    """
    return cast(PipelineRegistry, _registry)


def register_pipeline(pipeline: Pipeline) -> None:
    """Register a pipeline in the global registry.

    Args:
        pipeline: The pipeline to register
    """
    cast(PipelineRegistry, _registry).register(pipeline)


def get_pipeline(name: str) -> Pipeline:
    """Get a pipeline from the global registry.

    Args:
        name: The name of the pipeline to get

    Returns:
        The pipeline with the given name
    """
    result = cast(PipelineRegistry, _registry).get(name)
    if not result:
        raise KeyError(f"No pipeline registered with name '{name}'")
    return cast(Pipeline, result)


def create_pipeline(name: str, stages: list[PipelineStage] | None = None) -> Pipeline:
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
    name: str, input_data: Any, context: PipelineContext | None = None
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
    return pipeline.process(input_data, context)


class WorkflowComponent(ABC):
    """Base class for workflow components.

    A workflow component is a reusable unit of work that can be composed
    into pipelines. Components can be sources, processors, or sinks.
    """

    def __init__(
        self,
        component_id: str,
        name: str,
        component_type: str = ComponentType.PROCESSOR,
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize workflow component.

        Args:
            component_id: Unique component identifier
            name: Component name
            component_type: Component type
            config: Optional component configuration
            metadata: Optional component metadata
        """
        self.id = component_id
        self.name = name
        self.type = component_type
        self.config = config or {}
        self.metadata = metadata or {}

    @abstractmethod
    async def process(self, data: Any) -> Any:
        """Process input data.

        Args:
            data: Input data

        Returns:
            Processed data
        """
        pass


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
        self.id: str = ""
        self.name: str = ""
        self.components: list[WorkflowComponent] = []
        self.config: dict[str, Any] = {}
        self.status: ComponentType = ComponentType.SOURCE
        self.metadata: dict[str, Any] = {}

    def set_components(self, components: list[WorkflowComponent]) -> None:
        """Set workflow components.

        Args:
            components: List of workflow components
        """
        self.components = components

    def set_config(self, config: dict[str, Any]) -> None:
        """Set workflow configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        """Set workflow metadata.

        Args:
            metadata: Metadata dictionary
        """
        self.metadata = metadata


class WorkflowError(PepperpyError):
    """Base exception for workflow errors."""

    pass


class WorkflowProvider(PepperpyPlugin, ABC):
    """Base class for workflow providers.

    A workflow provider implements a specific type of workflow, such as:
    - Repository analysis
    - Content generation
    - Data processing
    - etc.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize workflow provider.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize workflow resources."""
        if self.initialized:
            return

        try:
            await self._initialize_resources()
            self.initialized = True
        except Exception as e:
            raise WorkflowError(f"Failed to initialize workflow: {e}") from e

    async def cleanup(self) -> None:
        """Clean up workflow resources."""
        if not self.initialized:
            return

        try:
            await self._cleanup_resources()
            self.initialized = False
        except Exception as e:
            raise WorkflowError(f"Failed to cleanup workflow: {e}") from e

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow.

        Args:
            input_data: Input data for the workflow

        Returns:
            Workflow execution results

        Raises:
            WorkflowError: If execution fails
        """
        pass

    async def _initialize_resources(self) -> None:
        """Initialize workflow resources.

        Override this method to implement custom resource initialization.
        """
        pass

    async def _cleanup_resources(self) -> None:
        """Clean up workflow resources.

        Override this method to implement custom resource cleanup.
        """
        pass


def create_provider(provider_type: str = "default", **config: Any) -> WorkflowProvider:
    """Create a workflow provider instance.

    Args:
        provider_type: Type of provider to create
        **config: Provider configuration

    Returns:
        Workflow provider instance

    Raises:
        ValidationError: If provider creation fails
    """
    try:
        provider = cast(
            WorkflowProvider,
            create_provider_instance("workflow", provider_type, **config),
        )
        return provider
    except Exception as e:
        raise ValidationError(f"Failed to create workflow provider: {e}") from e


class DocumentWorkflow(Workflow):
    """Workflow for document processing."""

    def __init__(self, input_data: str | Path) -> None:
        """Initialize document workflow.

        Args:
            input_data: Path to the document file or text content
        """
        self.id = "document_processing"
        self.name = "Document Processing"
        self.components = []
        self.config = {"input_data": str(input_data)}
        self.status = ComponentType.SOURCE
        self.metadata = {}


class WorkflowRegistry:
    """Registry for workflow components.

    This class manages the registration and retrieval of workflow
    components such as stages, processors, and transformers.
    """

    _instance = None

    def __new__(cls):
        """Create a new instance or return the existing one."""
        if cls._instance is None:
            cls._instance = super(WorkflowRegistry, cls).__new__(cls)
            cls._instance._components = {}
        return cls._instance

    def __init__(self):
        """Initialize registry."""
        if not hasattr(self, "_components"):
            self._components = {}

    def register(self, name: str, component: Any) -> None:
        """Register a workflow component.

        Args:
            name: Component name
            component: Component instance

        Raises:
            ValueError: If component is already registered
        """
        if name in self._components:
            raise ValueError(f"Component already registered: {name}")
        self._components[name] = component

    def get(self, name: str) -> Any | None:
        """Get a registered component.

        Args:
            name: Component name

        Returns:
            Component if found, None otherwise
        """
        return self._components.get(name)

    def list(self) -> dict[str, Any]:
        """List all registered components.

        Returns:
            Dictionary of component names and instances
        """
        return dict(self._components)

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            Registry summary
        """
        return f"Registry({len(self._components)} components)"


# Global registry instance
_registry = WorkflowRegistry()


def get_workflow_registry() -> WorkflowRegistry:
    """Get the global workflow registry.

    Returns:
        The global workflow registry
    """
    return cast(WorkflowRegistry, _registry)


def register_workflow(name: str, workflow: Any) -> None:
    """Register a workflow in the global registry.

    Args:
        name: Workflow name
        workflow: Workflow instance
    """
    cast(WorkflowRegistry, _registry).register(name=name, component=workflow)


def get_workflow(name: str) -> Any | None:
    """Get a workflow from the global registry.

    Args:
        name: Workflow name

    Returns:
        Workflow if found, None otherwise
    """
    return cast(WorkflowRegistry, _registry).get(name)


# Pipeline Stage Implementations
Input = TypeVar("Input")
Output = TypeVar("Output")
T = TypeVar("T")
R = TypeVar("R")


class FunctionStage(PipelineStage[Input, Output]):
    """Function-based pipeline stage.

    This stage wraps a function that processes input data and
    produces output data. The function can be synchronous or
    asynchronous.

    Attributes:
        name: The name of the stage
        func: The function to execute
        description: Optional description of the stage
    """

    def __init__(
        self,
        name: str,
        func: Callable[[Input, PipelineContext], Output],
        description: str | None = None,
    ):
        """Initialize a function stage.

        Args:
            name: The name of the stage
            func: The function to execute
            description: Optional description of the stage
        """
        super().__init__(name, description or "")
        self.func = func

    def process(self, input_data: Input, context: PipelineContext) -> Output:
        """Process the input data using the wrapped function.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            The processed output data
        """
        return self.func(input_data, context)


class TransformStage(PipelineStage[Input, Output]):
    """A pipeline stage that transforms input data using a transform object.

    This stage uses a transform object that has a transform method.
    """

    def __init__(
        self,
        name: str,
        transform: Any,
        description: str = "",
    ):
        """Initialize a transform stage.

        Args:
            name: The name of the stage
            transform: The transform object to use
            description: A description of the stage
        """
        super().__init__(name, description)
        self._transform = transform

    def process(self, input_data: Input, context: PipelineContext) -> Output:
        """Process the input data using the transform.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            The transformed output data
        """
        try:
            logger.debug(f"Executing transform stage: {self.name}")

            # If the transform is a string, look it up in the context
            if isinstance(self._transform, str):
                transform_name = self._transform
                transforms = context.get("transforms", {})
                if transform_name not in transforms:
                    raise PipelineError(
                        f"Transform '{transform_name}' not found in context"
                    )
                transform = transforms[transform_name]
            else:
                transform = self._transform

            # Call the transform method
            if hasattr(transform, "transform"):
                return transform.transform(input_data)
            elif callable(transform):
                return transform(input_data)
            else:
                raise PipelineError(
                    f"Invalid transform in stage {self.name}: {transform}"
                )

        except Exception as e:
            logger.error(f"Error in transform stage {self.name}: {e!s}")
            raise PipelineError(f"Error in transform stage {self.name}: {e!s}") from e


class ConditionalStage(PipelineStage[Input, Output]):
    """A pipeline stage that conditionally applies another stage.

    This stage applies a condition to the input data and, if the condition is
    met, applies another stage.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[Input, PipelineContext], bool],
        if_true: PipelineStage[Input, Output],
        if_false: PipelineStage[Input, Output] | None = None,
        description: str = "",
    ):
        """Initialize a conditional stage.

        Args:
            name: The name of the stage
            condition: The condition to check
            if_true: The stage to apply if the condition is true
            if_false: The stage to apply if the condition is false (optional)
            description: A description of the stage
        """
        super().__init__(name, description)
        self._condition = condition
        self._if_true = if_true
        self._if_false = if_false

    def process(self, input_data: Input, context: PipelineContext) -> Output:
        """Process the input data conditionally.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            The processed output data
        """
        try:
            logger.debug(f"Executing conditional stage: {self.name}")

            # Check the condition
            if self._condition(input_data, context):
                logger.debug(
                    f"Condition in stage {self.name} is true, using if_true stage"
                )
                return self._if_true(input_data, context)
            elif self._if_false is not None:
                logger.debug(
                    f"Condition in stage {self.name} is false, using if_false stage"
                )
                return self._if_false(input_data, context)
            else:
                logger.debug(
                    f"Condition in stage {self.name} is false, no if_false stage, returning input"
                )
                return cast(Output, input_data)
        except Exception as e:
            logger.error(f"Error in conditional stage {self.name}: {e!s}")
            raise PipelineError(f"Error in conditional stage {self.name}: {e!s}") from e
