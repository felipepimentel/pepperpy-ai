"""Transformation functionality for data module.

This module provides functionality for data transformation, including
transformers, pipelines, and stages. It consolidates the functionality
previously spread across multiple files.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from pepperpy.data.errors import TransformError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables for data types
T = TypeVar("T")
U = TypeVar("U")


#
# Core Transform Classes
#


class TransformType(Enum):
    """Type of transform."""

    FUNCTION = "function"
    CLASS = "class"
    PIPELINE = "pipeline"


class Transform(ABC):
    """Base class for data transformers.

    Data transformers are responsible for transforming data from one form to another.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform
        """
        pass

    @property
    @abstractmethod
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform
        """
        pass

    @abstractmethod
    def transform(self, data: Any) -> Any:
        """Transform data.

        Args:
            data: The data to transform

        Returns:
            The transformed data

        Raises:
            TransformError: If there is an error transforming the data
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary.

        Returns:
            The transform as a dictionary
        """
        pass


class FunctionTransform(Transform):
    """Transform based on a function.

    This transform uses a function to transform data.
    """

    def __init__(self, name: str, func: Callable[[Any], Any]):
        """Initialize a function transform.

        Args:
            name: The name of the transform
            func: The function to use for transformation
        """
        self._name = name
        self._func = func

    @property
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform
        """
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform
        """
        return TransformType.FUNCTION

    @property
    def func(self) -> Callable[[Any], Any]:
        """Get the function.

        Returns:
            The function
        """
        return self._func

    def transform(self, data: Any) -> Any:
        """Transform data.

        Args:
            data: The data to transform

        Returns:
            The transformed data

        Raises:
            TransformError: If there is an error transforming the data
        """
        try:
            return self._func(data)
        except Exception as e:
            raise TransformError(
                f"Error transforming data: {e}",
                transform_name=self.name,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary.

        Returns:
            The transform as a dictionary
        """
        return {
            "name": self.name,
            "type": self.transform_type.value,
            "function": self._func.__name__,
        }


class ClassTransform(Transform):
    """Transform based on a class.

    This transform uses a class to transform data.
    """

    def __init__(self, name: str, cls: Type[Any]):
        """Initialize a class transform.

        Args:
            name: The name of the transform
            cls: The class to use for transformation
        """
        self._name = name
        self._cls = cls

    @property
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform
        """
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform
        """
        return TransformType.CLASS

    @property
    def cls(self) -> Type[Any]:
        """Get the class.

        Returns:
            The class
        """
        return self._cls

    def transform(self, data: Any) -> Any:
        """Transform data.

        Args:
            data: The data to transform

        Returns:
            The transformed data

        Raises:
            TransformError: If there is an error transforming the data
        """
        try:
            return self._cls(data)
        except Exception as e:
            raise TransformError(
                f"Error transforming data: {e}",
                transform_name=self.name,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary.

        Returns:
            The transform as a dictionary
        """
        return {
            "name": self.name,
            "type": self.transform_type.value,
            "class": self._cls.__name__,
        }


class TransformPipeline(Transform):
    """Pipeline of transforms.

    This transform applies a sequence of transforms to data.
    """

    def __init__(self, name: str, transforms: List[Transform]):
        """Initialize a transform pipeline.

        Args:
            name: The name of the pipeline
            transforms: The transforms to apply
        """
        self._name = name
        self._transforms = transforms

    @property
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform
        """
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform
        """
        return TransformType.PIPELINE

    @property
    def transforms(self) -> List[Transform]:
        """Get the transforms.

        Returns:
            The transforms
        """
        return self._transforms

    def transform(self, data: Any) -> Any:
        """Transform data.

        Args:
            data: The data to transform

        Returns:
            The transformed data

        Raises:
            TransformError: If there is an error transforming the data
        """
        try:
            # Apply each transform in sequence
            result = data
            for transform in self._transforms:
                result = transform.transform(result)
            return result
        except TransformError as e:
            # Add context to the error
            raise TransformError(
                f"Error in pipeline '{self.name}': {e}",
                transform_name=self.name,
            )
        except Exception as e:
            # Convert other exceptions to TransformError
            raise TransformError(
                f"Error in pipeline '{self.name}': {e}",
                transform_name=self.name,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary.

        Returns:
            The transform as a dictionary
        """
        return {
            "name": self.name,
            "type": self.transform_type.value,
            "transforms": [t.name for t in self._transforms],
        }


class TransformRegistry:
    """Registry for transforms.

    This registry stores and retrieves transforms.
    """

    def __init__(self):
        """Initialize a transform registry."""
        self._transforms: Dict[str, Transform] = {}

    def register(self, transform: Transform) -> None:
        """Register a transform.

        Args:
            transform: The transform to register

        Raises:
            TransformError: If the transform is already registered
        """
        if transform.name in self._transforms:
            raise TransformError(f"Transform {transform.name} is already registered")

        self._transforms[transform.name] = transform

    def unregister(self, name: str) -> None:
        """Unregister a transform.

        Args:
            name: The name of the transform to unregister

        Raises:
            TransformError: If the transform is not registered
        """
        if name not in self._transforms:
            raise TransformError(f"Transform {name} is not registered")

        del self._transforms[name]

    def get(self, name: str) -> Transform:
        """Get a transform.

        Args:
            name: The name of the transform to get

        Returns:
            The transform

        Raises:
            TransformError: If the transform is not registered
        """
        if name not in self._transforms:
            raise TransformError(f"Transform {name} is not registered")

        return self._transforms[name]

    def list(self) -> List[str]:
        """List registered transforms.

        Returns:
            The names of registered transforms
        """
        return list(self._transforms.keys())

    def clear(self) -> None:
        """Clear the registry."""
        self._transforms.clear()


# Global transform registry
_registry: Optional[TransformRegistry] = None


def get_registry() -> TransformRegistry:
    """Get the global transform registry.

    Returns:
        The global transform registry
    """
    global _registry
    if _registry is None:
        _registry = TransformRegistry()
    return _registry


def set_registry(registry: TransformRegistry) -> None:
    """Set the global transform registry.

    Args:
        registry: The transform registry to set
    """
    global _registry
    _registry = registry


def register_transform(transform: Transform) -> None:
    """Register a transform.

    Args:
        transform: The transform to register

    Raises:
        TransformError: If the transform is already registered
    """
    get_registry().register(transform)


def unregister_transform(name: str) -> None:
    """Unregister a transform.

    Args:
        name: The name of the transform to unregister

    Raises:
        TransformError: If the transform is not registered
    """
    get_registry().unregister(name)


def get_transform(name: str) -> Transform:
    """Get a transform.

    Args:
        name: The name of the transform to get

    Returns:
        The transform

    Raises:
        TransformError: If the transform is not registered
    """
    return get_registry().get(name)


def list_transforms() -> List[str]:
    """List registered transforms.

    Returns:
        The names of registered transforms
    """
    return get_registry().list()


def clear_transforms() -> None:
    """Clear all registered transforms."""
    get_registry().clear()


def register_function_transform(name: str, func: Callable[[Any], Any]) -> None:
    """Register a function transform.

    Args:
        name: The name of the transform
        func: The function to use for transformation

    Raises:
        TransformError: If the transform is already registered
    """
    transform = FunctionTransform(name, func)
    register_transform(transform)


def register_class_transform(name: str, cls: Type[Any]) -> None:
    """Register a class transform.

    Args:
        name: The name of the transform
        cls: The class to use for transformation

    Raises:
        TransformError: If the transform is already registered
    """
    transform = ClassTransform(name, cls)
    register_transform(transform)


def register_pipeline(name: str, transforms: List[Union[Transform, str]]) -> None:
    """Register a transform pipeline.

    Args:
        name: The name of the pipeline
        transforms: The transforms to apply, either as Transform objects or the names of registered transforms

    Raises:
        TransformError: If the pipeline is already registered
        TransformError: If a named transform is not registered
    """
    # Resolve transform names to objects
    resolved_transforms = []
    for t in transforms:
        if isinstance(t, str):
            resolved_transforms.append(get_transform(t))
        else:
            resolved_transforms.append(t)

    # Create and register the pipeline
    pipeline = TransformPipeline(name, resolved_transforms)
    register_transform(pipeline)


def transform(data: Any, transform_name: str) -> Any:
    """Transform data using a registered transform.

    Args:
        data: The data to transform
        transform_name: The name of the transform to use

    Returns:
        The transformed data

    Raises:
        TransformError: If the transform is not registered
        TransformError: If there is an error transforming the data
    """
    t = get_transform(transform_name)
    return t.transform(data)


#
# Pipeline Classes
#


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
    """Pipeline for data transformation.

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
            context: The pipeline context, or None to create a new context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error executing the pipeline
        """
        try:
            # Create a new context if none is provided
            if context is None:
                context = {}

            # Add the pipeline to the context
            context["pipeline"] = self.name

            # Apply each stage in sequence
            result = data
            for stage in self._stages:
                result = stage.process(result, context)

            return result
        except TransformError as e:
            # Add context to the error
            raise TransformError(
                f"Error in pipeline '{self.name}': {e}",
                transform_name=self.name,
            )
        except Exception as e:
            # Convert other exceptions to TransformError
            raise TransformError(
                f"Error in pipeline '{self.name}': {e}",
                transform_name=self.name,
            )


class PipelineRegistry:
    """Registry for pipelines.

    This registry stores and retrieves pipelines.
    """

    def __init__(self):
        """Initialize a pipeline registry."""
        self._pipelines: Dict[str, Pipeline] = {}

    def register(self, pipeline: Pipeline) -> None:
        """Register a pipeline.

        Args:
            pipeline: The pipeline to register

        Raises:
            TransformError: If the pipeline is already registered
        """
        if pipeline.name in self._pipelines:
            raise TransformError(f"Pipeline {pipeline.name} is already registered")

        self._pipelines[pipeline.name] = pipeline

    def unregister(self, name: str) -> None:
        """Unregister a pipeline.

        Args:
            name: The name of the pipeline to unregister

        Raises:
            TransformError: If the pipeline is not registered
        """
        if name not in self._pipelines:
            raise TransformError(f"Pipeline {name} is not registered")

        del self._pipelines[name]

    def get(self, name: str) -> Pipeline:
        """Get a pipeline.

        Args:
            name: The name of the pipeline to get

        Returns:
            The pipeline

        Raises:
            TransformError: If the pipeline is not registered
        """
        if name not in self._pipelines:
            raise TransformError(f"Pipeline {name} is not registered")

        return self._pipelines[name]

    def list(self) -> List[str]:
        """List registered pipelines.

        Returns:
            The names of registered pipelines
        """
        return list(self._pipelines.keys())

    def clear(self) -> None:
        """Clear the registry."""
        self._pipelines.clear()


# Global pipeline registry
_pipeline_registry: Optional[PipelineRegistry] = None


def get_pipeline_registry() -> PipelineRegistry:
    """Get the global pipeline registry.

    Returns:
        The global pipeline registry
    """
    global _pipeline_registry
    if _pipeline_registry is None:
        _pipeline_registry = PipelineRegistry()
    return _pipeline_registry


def set_pipeline_registry(registry: PipelineRegistry) -> None:
    """Set the global pipeline registry.

    Args:
        registry: The pipeline registry to set
    """
    global _pipeline_registry
    _pipeline_registry = registry


def register_pipeline_obj(pipeline: Pipeline) -> None:
    """Register a pipeline.

    Args:
        pipeline: The pipeline to register

    Raises:
        TransformError: If the pipeline is already registered
    """
    get_pipeline_registry().register(pipeline)


def unregister_pipeline(name: str) -> None:
    """Unregister a pipeline.

    Args:
        name: The name of the pipeline to unregister

    Raises:
        TransformError: If the pipeline is not registered
    """
    get_pipeline_registry().unregister(name)


def get_pipeline(name: str) -> Pipeline:
    """Get a pipeline.

    Args:
        name: The name of the pipeline to get

    Returns:
        The pipeline

    Raises:
        TransformError: If the pipeline is not registered
    """
    return get_pipeline_registry().get(name)


def list_pipelines() -> List[str]:
    """List registered pipelines.

    Returns:
        The names of registered pipelines
    """
    return get_pipeline_registry().list()


def clear_pipelines() -> None:
    """Clear all registered pipelines."""
    get_pipeline_registry().clear()


def create_pipeline(name: str, stages: List[PipelineStage]) -> Pipeline:
    """Create a pipeline.

    Args:
        name: The name of the pipeline
        stages: The stages to apply

    Returns:
        The created pipeline
    """
    return Pipeline(name, stages)


def execute_pipeline(
    name: str, data: Any, context: Optional[Dict[str, Any]] = None
) -> Any:
    """Execute a registered pipeline.

    Args:
        name: The name of the pipeline to execute
        data: The data to process
        context: The pipeline context, or None to create a new context

    Returns:
        The processed data

    Raises:
        TransformError: If the pipeline is not registered
        TransformError: If there is an error executing the pipeline
    """
    pipeline = get_pipeline(name)
    return pipeline.execute(data, context)


def flatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        data: The dictionary to flatten
        separator: The separator to use for nested keys

    Returns:
        The flattened dictionary

    Example:
        >>> data = {"a": {"b": 1, "c": {"d": 2}}}
        >>> flatten(data)
        {"a.b": 1, "a.c.d": 2}
    """
    result = {}

    def _flatten(d: Dict[str, Any], prefix: str = "") -> None:
        for key, value in d.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            if isinstance(value, dict):
                _flatten(value, new_key)
            else:
                result[new_key] = value

    _flatten(data)
    return result


def jsonify(data: Any) -> Any:
    """Convert data to JSON-serializable format.

    Args:
        data: The data to convert

    Returns:
        The JSON-serializable data

    Example:
        >>> from datetime import datetime
        >>> data = {"date": datetime(2024, 1, 1)}
        >>> jsonify(data)
        {"date": "2024-01-01T00:00:00"}
    """
    if isinstance(data, (date, datetime)):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: jsonify(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        return [jsonify(item) for item in data]
    elif hasattr(data, "to_dict"):
        return jsonify(data.to_dict())
    return data


def map_data(data: List[T], func: callable) -> List[U]:
    """Map a function over a list of data.

    Args:
        data: The list of data to transform
        func: The function to apply to each item

    Returns:
        The transformed list

    Example:
        >>> data = [1, 2, 3]
        >>> map_data(data, lambda x: x * 2)
        [2, 4, 6]
    """
    try:
        return [func(item) for item in data]
    except Exception as e:
        raise TransformError(f"Error mapping data: {str(e)}")


def merge(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries.

    Args:
        *dicts: The dictionaries to merge

    Returns:
        The merged dictionary

    Example:
        >>> d1 = {"a": 1}
        >>> d2 = {"b": 2}
        >>> merge(d1, d2)
        {"a": 1, "b": 2}
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def normalize(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize data according to a schema.

    Args:
        data: The data to normalize
        schema: The schema to normalize against

    Returns:
        The normalized data

    Example:
        >>> data = {"name": "John ", "age": "30"}
        >>> schema = {"name": str, "age": int}
        >>> normalize(data, schema)
        {"name": "John", "age": 30}
    """
    result = {}
    for key, value in data.items():
        if key in schema:
            try:
                # Get expected type
                expected_type = schema[key]

                # Apply type conversion
                if expected_type == str:
                    result[key] = str(value).strip()
                elif expected_type == int:
                    result[key] = int(value)
                elif expected_type == float:
                    result[key] = float(value)
                elif expected_type == bool:
                    result[key] = bool(value)
                else:
                    result[key] = value
            except (ValueError, TypeError) as e:
                raise TransformError(f"Error normalizing field {key}: {str(e)}")
    return result


def parse_date(value: Union[str, datetime, date]) -> date:
    """Parse a date from various formats.

    Args:
        value: The date to parse

    Returns:
        The parsed date

    Example:
        >>> parse_date("2024-01-01")
        datetime.date(2024, 1, 1)
    """
    if isinstance(value, datetime):
        return value.date()
    elif isinstance(value, date):
        return value
    elif isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            raise TransformError(f"Invalid date format: {value}")
    else:
        raise TransformError(f"Cannot parse date from type: {type(value)}")


def parse_datetime(value: Union[str, datetime]) -> datetime:
    """Parse a datetime from various formats.

    Args:
        value: The datetime to parse

    Returns:
        The parsed datetime

    Example:
        >>> parse_datetime("2024-01-01T12:00:00")
        datetime.datetime(2024, 1, 1, 12, 0)
    """
    if isinstance(value, datetime):
        return value
    elif isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise TransformError(f"Invalid datetime format: {value}")
    else:
        raise TransformError(f"Cannot parse datetime from type: {type(value)}")
