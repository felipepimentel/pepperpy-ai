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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union, cast

# Importe a classe de erro do módulo correto com a grafia correta
from pepperpy.core import PepperpyError
from pepperpy.core.errors import ValidationError
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.manager import create_provider_instance

# Type variables for generic pipeline stages
Input = TypeVar("Input")
Output = TypeVar("Output")
T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger(__name__)

__all__ = [
    "ComponentType",
    "PipelineError",
    "PipelineContext",
    "PipelineConfig",
    "PipelineStage",
    "Pipeline",
    "PipelineRegistry",
    "WorkflowComponent",
    "Workflow",
    "WorkflowProvider",
    "DocumentWorkflow",
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
        self, input_data: Input, context: Optional[PipelineContext] = None
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
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
        self.components: List[WorkflowComponent] = []
        self.config: Dict[str, Any] = {}
        self.status: ComponentType = ComponentType.SOURCE
        self.metadata: Dict[str, Any] = {}

    def set_components(self, components: List[WorkflowComponent]) -> None:
        """Set workflow components.

        Args:
            components: List of workflow components
        """
        self.components = components

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set workflow configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set workflow metadata.

        Args:
            metadata: Metadata dictionary
        """
        self.metadata = metadata


class WorkflowProvider(PepperpyPlugin):
    """Base class for workflow providers.

    A workflow provider is responsible for executing workflows and managing
    their lifecycle. It provides methods for creating, executing, and
    monitoring workflows.
    """

    def __init__(
        self,
        name: str = "workflow",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize workflow provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name=name, config=config, **kwargs)
        self._workflows: Dict[str, Workflow] = {}

    @abstractmethod
    async def create_workflow(
        self,
        name: str,
        components: List[WorkflowComponent],
        config: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """Create a new workflow.

        Args:
            name: Workflow name
            components: List of workflow components
            config: Optional workflow configuration

        Returns:
            Created workflow instance
        """
        pass

    @abstractmethod
    async def execute_workflow(
        self,
        workflow: Workflow,
        input_data: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute
            input_data: Optional input data
            config: Optional execution configuration

        Returns:
            Workflow execution result
        """
        pass

    @abstractmethod
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow instance or None if not found
        """
        pass

    @abstractmethod
    async def list_workflows(self) -> List[Workflow]:
        """List all workflows.

        Returns:
            List of workflows
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

    def __init__(self, input_data: Union[str, Path]) -> None:
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
