"""Pipeline functionality for data transformation.

This module provides pipeline functionality for data transformation,
including pipeline stages and execution.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from pepperpy.data.errors import TransformError
from pepperpy.data.transform.core import Transform, get_transform
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for data types
T = TypeVar("T")
U = TypeVar("U")


class PipelineStage(ABC):
    """Base class for pipeline stages.

    Pipeline stages are responsible for processing data in a pipeline.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the stage.

        Returns:
            The name of the stage
        """
        pass

    @abstractmethod
    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """Process data.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error processing the data
        """
        pass


class TransformStage(PipelineStage):
    """Pipeline stage that applies a transform.

    This stage applies a transform to data.
    """

    def __init__(self, name: str, transform: Union[Transform, str]):
        """Initialize a transform stage.

        Args:
            name: The name of the stage
            transform: The transform to apply, either as a Transform object or the name of a registered transform
        """
        self._name = name
        self._transform = transform

    @property
    def name(self) -> str:
        """Get the name of the stage.

        Returns:
            The name of the stage
        """
        return self._name

    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """Process data.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error processing the data
        """
        try:
            # Get the transform
            transform_obj = self._transform
            if isinstance(transform_obj, str):
                transform_obj = get_transform(transform_obj)

            # Apply the transform
            result = transform_obj.transform(data)

            # Update the context
            context["last_stage"] = self.name
            context["last_result"] = result

            return result
        except TransformError as e:
            raise TransformError(
                f"Error in stage '{self.name}': {e}",
                transform_name=self.name,
            )
        except Exception as e:
            raise TransformError(
                f"Error in stage '{self.name}': {e}",
                transform_name=self.name,
            )


class FunctionStage(PipelineStage):
    """Pipeline stage that applies a function.

    This stage applies a function to data.
    """

    def __init__(self, name: str, func: Callable[[Any, Dict[str, Any]], Any]):
        """Initialize a function stage.

        Args:
            name: The name of the stage
            func: The function to apply
        """
        self._name = name
        self._func = func

    @property
    def name(self) -> str:
        """Get the name of the stage.

        Returns:
            The name of the stage
        """
        return self._name

    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """Process data.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error processing the data
        """
        try:
            # Apply the function
            result = self._func(data, context)

            # Update the context
            context["last_stage"] = self.name
            context["last_result"] = result

            return result
        except Exception as e:
            raise TransformError(
                f"Error in stage '{self.name}': {e}",
                transform_name=self.name,
            )


class ConditionalStage(PipelineStage):
    """Pipeline stage that conditionally applies a stage.

    This stage applies a stage if a condition is met.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[Any, Dict[str, Any]], bool],
        stage: PipelineStage,
        else_stage: Optional[PipelineStage] = None,
    ):
        """Initialize a conditional stage.

        Args:
            name: The name of the stage
            condition: The condition to check
            stage: The stage to apply if the condition is met
            else_stage: The stage to apply if the condition is not met
        """
        self._name = name
        self._condition = condition
        self._stage = stage
        self._else_stage = else_stage

    @property
    def name(self) -> str:
        """Get the name of the stage.

        Returns:
            The name of the stage
        """
        return self._name

    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """Process data.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error processing the data
        """
        try:
            # Check the condition
            if self._condition(data, context):
                # Apply the stage
                result = self._stage.process(data, context)
            elif self._else_stage is not None:
                # Apply the else stage
                result = self._else_stage.process(data, context)
            else:
                # No else stage, return the data as is
                result = data

            # Update the context
            context["last_stage"] = self.name
            context["last_result"] = result

            return result
        except TransformError as e:
            raise TransformError(
                f"Error in stage '{self.name}': {e}",
                transform_name=self.name,
            )
        except Exception as e:
            raise TransformError(
                f"Error in stage '{self.name}': {e}",
                transform_name=self.name,
            )


class Pipeline:
    """Data transformation pipeline.

    This pipeline applies a sequence of stages to data.
    """

    def __init__(self, name: str, stages: List[PipelineStage]):
        """Initialize a pipeline.

        Args:
            name: The name of the pipeline
            stages: The stages to apply
        """
        self._name = name
        self._stages = stages

    @property
    def name(self) -> str:
        """Get the name of the pipeline.

        Returns:
            The name of the pipeline
        """
        return self._name

    @property
    def stages(self) -> List[PipelineStage]:
        """Get the stages.

        Returns:
            The stages
        """
        return self._stages

    def execute(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute the pipeline.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error processing the data
        """
        # Initialize the context
        if context is None:
            context = {}

        context["pipeline"] = self.name
        context["start_time"] = context.get("start_time", None)

        # Process the data
        result = data

        for stage in self._stages:
            try:
                result = stage.process(result, context)
            except TransformError as e:
                raise TransformError(
                    f"Error in pipeline '{self.name}' at stage '{stage.name}': {e}",
                    transform_name=self.name,
                )
            except Exception as e:
                raise TransformError(
                    f"Error in pipeline '{self.name}' at stage '{stage.name}': {e}",
                    transform_name=self.name,
                )

        return result


class PipelineRegistry:
    """Registry for pipelines.

    The pipeline registry is responsible for managing pipelines.
    """

    def __init__(self):
        """Initialize a pipeline registry."""
        self._pipelines: Dict[str, Pipeline] = {}

    def register(self, pipeline: Pipeline) -> None:
        """Register a pipeline.

        Args:
            pipeline: The pipeline to register

        Raises:
            TransformError: If a pipeline with the same name is already registered
        """
        if pipeline.name in self._pipelines:
            raise TransformError(f"Pipeline '{pipeline.name}' is already registered")

        self._pipelines[pipeline.name] = pipeline

    def unregister(self, name: str) -> None:
        """Unregister a pipeline.

        Args:
            name: The name of the pipeline to unregister

        Raises:
            TransformError: If the pipeline is not registered
        """
        if name not in self._pipelines:
            raise TransformError(f"Pipeline '{name}' is not registered")

        del self._pipelines[name]

    def get(self, name: str) -> Pipeline:
        """Get a pipeline by name.

        Args:
            name: The name of the pipeline

        Returns:
            The pipeline

        Raises:
            TransformError: If the pipeline is not registered
        """
        if name not in self._pipelines:
            raise TransformError(f"Pipeline '{name}' is not registered")

        return self._pipelines[name]

    def list(self) -> List[str]:
        """List all registered pipelines.

        Returns:
            The names of all registered pipelines
        """
        return list(self._pipelines.keys())

    def clear(self) -> None:
        """Clear all registered pipelines."""
        self._pipelines.clear()


# Default pipeline registry
_registry = PipelineRegistry()


def get_registry() -> PipelineRegistry:
    """Get the default pipeline registry.

    Returns:
        The default pipeline registry
    """
    return _registry


def set_registry(registry: PipelineRegistry) -> None:
    """Set the default pipeline registry.

    Args:
        registry: The pipeline registry to set as the default
    """
    global _registry
    _registry = registry


def register_pipeline(pipeline: Pipeline) -> None:
    """Register a pipeline in the default registry.

    Args:
        pipeline: The pipeline to register

    Raises:
        TransformError: If a pipeline with the same name is already registered
    """
    get_registry().register(pipeline)


def unregister_pipeline(name: str) -> None:
    """Unregister a pipeline from the default registry.

    Args:
        name: The name of the pipeline to unregister

    Raises:
        TransformError: If the pipeline is not registered
    """
    get_registry().unregister(name)


def get_pipeline(name: str) -> Pipeline:
    """Get a pipeline by name from the default registry.

    Args:
        name: The name of the pipeline

    Returns:
        The pipeline

    Raises:
        TransformError: If the pipeline is not registered
    """
    return get_registry().get(name)


def list_pipelines() -> List[str]:
    """List all registered pipelines in the default registry.

    Returns:
        The names of all registered pipelines
    """
    return get_registry().list()


def clear_pipelines() -> None:
    """Clear all registered pipelines in the default registry."""
    get_registry().clear()


def create_pipeline(name: str, stages: List[PipelineStage]) -> Pipeline:
    """Create a pipeline.

    Args:
        name: The name of the pipeline
        stages: The stages to apply

    Returns:
        The pipeline
    """
    return Pipeline(name, stages)


def execute_pipeline(
    name: str, data: Any, context: Optional[Dict[str, Any]] = None
) -> Any:
    """Execute a pipeline.

    Args:
        name: The name of the pipeline
        data: The data to process
        context: The pipeline context

    Returns:
        The processed data

    Raises:
        TransformError: If the pipeline is not registered
        TransformError: If there is an error processing the data
    """
    pipeline = get_pipeline(name)
    return pipeline.execute(data, context)
