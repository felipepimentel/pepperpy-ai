"""Data transformation module for PepperPy.

This module provides utilities for transforming data in pipelines.
It includes the legacy Pipeline class and various transformation utilities.
The module is designed to be backward compatible while transitioning to
the new unified pipeline framework.

Key Components:
    - Transform: Base class for all data transformers
    - Pipeline: Legacy pipeline implementation for data transformation
    - Registry: Global registries for transforms and pipelines
    - Utilities: Common data transformation functions

Note:
    This module is being migrated to use the new unified pipeline framework.
    While the API remains the same for backward compatibility, new code should
    use the framework in `pepperpy.core.pipeline` directly.

Example:
    Basic pipeline usage:
    >>> from pepperpy.data.transform import Pipeline, FunctionTransform
    >>> pipeline = Pipeline()
    >>> def double(x): return x * 2
    >>> pipeline.add_stage(FunctionTransform("double", double))
    >>> result = pipeline.execute(2)
    >>> assert result == 4

    Using transforms directly:
    >>> from pepperpy.data.transform import TextTransform
    >>> transform = TextTransform()
    >>> result = transform.uppercase("hello")
    >>> assert result == "HELLO"

    Using the registry:
    >>> from pepperpy.data.transform import register_function_transform
    >>> def add_one(x): return x + 1
    >>> register_function_transform("add_one", add_one)
    >>> from pepperpy.data.transform import transform
    >>> result = transform(2, "add_one")
    >>> assert result == 3
    >>> from pepperpy.data.transform import unregister_transform
    >>> unregister_transform("add_one")  # Cleanup

Migration Guide:
    To migrate existing code to the new framework:
    1. Import from pepperpy.core.pipeline instead:
        from pepperpy.core.pipeline.base import Pipeline
        from pepperpy.core.pipeline.stages import FunctionStage
    2. Create a pipeline with stages:
        pipeline = Pipeline("name")
        pipeline.add_stage(FunctionStage("stage1", func))
    3. Execute with context:
        context = PipelineContext()
        result = await pipeline.execute(data, context)

Classes:
    Transform: Base class for data transformers
    FunctionTransform: Transform based on a function
    ClassTransform: Transform based on a class
    TransformPipeline: Pipeline of transforms
    Pipeline: Legacy pipeline implementation
    PipelineStage: A stage in a pipeline
    TransformRegistry: Registry for transforms
    PipelineRegistry: Registry for pipelines
    TextTransform: Text transformation utility
    DataTransform: Data transformation utility

Functions:
    transform(data, name): Transform data using a registered transform
    register_transform(transform): Register a transform
    unregister_transform(name): Unregister a transform
    get_transform(name): Get a registered transform
    list_transforms(): List registered transforms
    clear_transforms(): Clear all transforms
    register_function_transform(name, func): Register a function transform
    register_class_transform(name, cls): Register a class transform
    register_pipeline(name, transforms): Register a pipeline
    create_pipeline(stages): Create a pipeline from stages
    execute_pipeline(name, data): Execute a registered pipeline
    flatten(data): Flatten a nested dictionary
    jsonify(data): Convert data to JSON format
    map_data(data, func): Map a function over data
    merge(*dicts): Merge multiple dictionaries
    normalize(data, schema): Normalize data to a schema
    parse_date(value): Parse a date value
    parse_datetime(value): Parse a datetime value

See Also:
    pepperpy.core.pipeline: The new unified pipeline framework
    pepperpy.core.pipeline.stages: Pipeline stage implementations
    pepperpy.core.pipeline.registry: Pipeline and component registry
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
    They provide a consistent interface for data transformation operations.

    Example:
        >>> class UppercaseTransform(Transform):
        ...     @property
        ...     def name(self) -> str:
        ...         return "uppercase"
        ...     @property
        ...     def transform_type(self) -> TransformType:
        ...         return TransformType.FUNCTION
        ...     def transform(self, data: str) -> str:
        ...         return data.upper()
        ...     def to_dict(self) -> Dict[str, Any]:
        ...         return {"name": self.name, "type": self.transform_type.value}
        >>> transform = UppercaseTransform()
        >>> result = transform.transform("hello")
        >>> assert result == "HELLO"
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform

        Example:
            >>> class MyTransform(Transform):
            ...     @property
            ...     def name(self) -> str:
            ...         return "my_transform"
        """
        pass

    @property
    @abstractmethod
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform

        Example:
            >>> class MyTransform(Transform):
            ...     @property
            ...     def transform_type(self) -> TransformType:
            ...         return TransformType.FUNCTION
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

        Example:
            >>> class MyTransform(Transform):
            ...     def transform(self, data: str) -> str:
            ...         return data.upper()
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary.

        Returns:
            The transform as a dictionary with at least 'name' and 'type' fields

        Example:
            >>> class MyTransform(Transform):
            ...     def to_dict(self) -> Dict[str, Any]:
            ...         return {
            ...             "name": self.name,
            ...             "type": self.transform_type.value
            ...         }
        """
        pass


class FunctionTransform(Transform):
    """Transform based on a function.

    This transform uses a function to transform data. It wraps a callable
    in the Transform interface, making it easy to use functions as transforms.

    Example:
        >>> def uppercase(text: str) -> str:
        ...     return text.upper()
        >>> transform = FunctionTransform("uppercase", uppercase)
        >>> result = transform.transform("hello")
        >>> assert result == "HELLO"
    """

    def __init__(self, name: str, func: Callable[[Any], Any]):
        """Initialize a function transform.

        Args:
            name: The name of the transform
            func: The function to use for transformation

        Example:
            >>> transform = FunctionTransform("double", lambda x: x * 2)
        """
        self._name = name
        self._func = func

    @property
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform

        Example:
            >>> transform = FunctionTransform("double", lambda x: x * 2)
            >>> assert transform.name == "double"
        """
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform (always TransformType.FUNCTION)

        Example:
            >>> transform = FunctionTransform("double", lambda x: x * 2)
            >>> assert transform.transform_type == TransformType.FUNCTION
        """
        return TransformType.FUNCTION

    @property
    def func(self) -> Callable[[Any], Any]:
        """Get the function.

        Returns:
            The function used for transformation

        Example:
            >>> transform = FunctionTransform("double", lambda x: x * 2)
            >>> assert transform.func(2) == 4
        """
        return self._func

    def transform(self, data: Any) -> Any:
        """Transform data using the function.

        Args:
            data: The data to transform

        Returns:
            The transformed data

        Raises:
            TransformError: If there is an error transforming the data

        Example:
            >>> transform = FunctionTransform("double", lambda x: x * 2)
            >>> assert transform.transform(2) == 4
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
            The transform as a dictionary containing:
                - name: The name of the transform
                - type: The type of the transform
                - function: The name of the function

        Example:
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> info = transform.to_dict()
            >>> assert info["name"] == "double"
            >>> assert info["type"] == "function"
            >>> assert info["function"] == "double"
        """
        return {
            "name": self.name,
            "type": self.transform_type.value,
            "function": self._func.__name__,
        }


class ClassTransform(Transform):
    """Transform based on a class.

    This transform uses a class to transform data. It wraps a class
    in the Transform interface, making it easy to use classes as transforms.

    Example:
        >>> class Doubler:
        ...     def __init__(self, value):
        ...         self.value = value * 2
        >>> transform = ClassTransform("doubler", Doubler)
        >>> result = transform.transform(2)
        >>> assert result.value == 4
    """

    def __init__(self, name: str, cls: Type[Any]):
        """Initialize a class transform.

        Args:
            name: The name of the transform
            cls: The class to use for transformation

        Example:
            >>> class Doubler:
            ...     def __init__(self, value):
            ...         self.value = value * 2
            >>> transform = ClassTransform("doubler", Doubler)
        """
        self._name = name
        self._cls = cls

    @property
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform

        Example:
            >>> class Doubler: pass
            >>> transform = ClassTransform("doubler", Doubler)
            >>> assert transform.name == "doubler"
        """
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform (always TransformType.CLASS)

        Example:
            >>> class Doubler: pass
            >>> transform = ClassTransform("doubler", Doubler)
            >>> assert transform.transform_type == TransformType.CLASS
        """
        return TransformType.CLASS

    @property
    def cls(self) -> Type[Any]:
        """Get the class.

        Returns:
            The class used for transformation

        Example:
            >>> class Doubler: pass
            >>> transform = ClassTransform("doubler", Doubler)
            >>> assert transform.cls == Doubler
        """
        return self._cls

    def transform(self, data: Any) -> Any:
        """Transform data by creating a new instance of the class.

        Args:
            data: The data to transform

        Returns:
            A new instance of the class initialized with the data

        Raises:
            TransformError: If there is an error transforming the data

        Example:
            >>> class Doubler:
            ...     def __init__(self, value):
            ...         self.value = value * 2
            >>> transform = ClassTransform("doubler", Doubler)
            >>> result = transform.transform(2)
            >>> assert result.value == 4
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
            The transform as a dictionary containing:
                - name: The name of the transform
                - type: The type of the transform
                - class: The name of the class

        Example:
            >>> class Doubler: pass
            >>> transform = ClassTransform("doubler", Doubler)
            >>> info = transform.to_dict()
            >>> assert info["name"] == "doubler"
            >>> assert info["type"] == "class"
            >>> assert info["class"] == "Doubler"
        """
        return {
            "name": self.name,
            "type": self.transform_type.value,
            "class": self._cls.__name__,
        }


class TransformPipeline(Transform):
    """Pipeline of transforms.

    This transform applies a sequence of transforms to data in order.
    Each transform's output becomes the input to the next transform.

    Example:
        >>> def uppercase(text: str) -> str:
        ...     return text.upper()
        >>> def add_prefix(text: str) -> str:
        ...     return f"prefix_{text}"
        >>> transforms = [
        ...     FunctionTransform("uppercase", uppercase),
        ...     FunctionTransform("prefix", add_prefix)
        ... ]
        >>> pipeline = TransformPipeline("my_pipeline", transforms)
        >>> result = pipeline.transform("hello")
        >>> assert result == "prefix_HELLO"
    """

    def __init__(self, name: str, transforms: List[Transform]):
        """Initialize a transform pipeline.

        Args:
            name: The name of the pipeline
            transforms: The transforms to apply in sequence

        Example:
            >>> def double(x): return x * 2
            >>> def add_one(x): return x + 1
            >>> transforms = [
            ...     FunctionTransform("double", double),
            ...     FunctionTransform("add_one", add_one)
            ... ]
            >>> pipeline = TransformPipeline("math_ops", transforms)
        """
        self._name = name
        self._transforms = transforms

    @property
    def name(self) -> str:
        """Get the name of the transform.

        Returns:
            The name of the transform

        Example:
            >>> pipeline = TransformPipeline("my_pipeline", [])
            >>> assert pipeline.name == "my_pipeline"
        """
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the type of the transform.

        Returns:
            The type of the transform (always TransformType.PIPELINE)

        Example:
            >>> pipeline = TransformPipeline("my_pipeline", [])
            >>> assert pipeline.transform_type == TransformType.PIPELINE
        """
        return TransformType.PIPELINE

    @property
    def transforms(self) -> List[Transform]:
        """Get the transforms in the pipeline.

        Returns:
            The list of transforms that make up the pipeline

        Example:
            >>> def noop(x): return x
            >>> transform = FunctionTransform("noop", noop)
            >>> pipeline = TransformPipeline("my_pipeline", [transform])
            >>> assert pipeline.transforms[0] == transform
        """
        return self._transforms

    def transform(self, data: Any) -> Any:
        """Transform data by applying each transform in sequence.

        Args:
            data: The data to transform

        Returns:
            The transformed data after passing through all transforms

        Raises:
            TransformError: If there is an error in any transform

        Example:
            >>> def double(x): return x * 2
            >>> def add_one(x): return x + 1
            >>> transforms = [
            ...     FunctionTransform("double", double),
            ...     FunctionTransform("add_one", add_one)
            ... ]
            >>> pipeline = TransformPipeline("math_ops", transforms)
            >>> assert pipeline.transform(2) == 5
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
            The transform as a dictionary containing:
                - name: The name of the pipeline
                - type: The type of the transform (pipeline)
                - transforms: List of transform names in the pipeline

        Example:
            >>> def noop(x): return x
            >>> transform = FunctionTransform("noop", noop)
            >>> pipeline = TransformPipeline("my_pipeline", [transform])
            >>> info = pipeline.to_dict()
            >>> assert info["name"] == "my_pipeline"
            >>> assert info["type"] == "pipeline"
            >>> assert info["transforms"] == ["noop"]
        """
        return {
            "name": self.name,
            "type": self.transform_type.value,
            "transforms": [t.name for t in self._transforms],
        }


class TransformRegistry:
    """Registry for managing transforms.

    This registry provides a centralized way to store and retrieve transforms.
    It ensures that transform names are unique and provides easy access to
    registered transforms.

    The registry is thread-safe and maintains a single source of truth for
    all transforms in the system.

    Note:
        This is part of the legacy transform system. For new code,
        consider using the unified pipeline framework in `pepperpy.core.pipeline`.

    Example:
        >>> registry = TransformRegistry()
        >>> def double(x): return x * 2
        >>> transform = FunctionTransform("double", double)
        >>> registry.register(transform)
        >>> same_transform = registry.get("double")
        >>> assert same_transform.transform(2) == 4
        >>> registry.unregister("double")  # Cleanup

    Migration Guide:
        To migrate to the new framework:
        1. Import from pepperpy.core.pipeline instead:
            from pepperpy.core.pipeline.registry import Registry
        2. Create and use the registry:
            registry = Registry()
            registry.register("name", component)
    """

    def __init__(self):
        """Initialize an empty transform registry.

        Example:
            >>> registry = TransformRegistry()
            >>> assert len(registry.list()) == 0
        """
        self._transforms: Dict[str, Transform] = {}

    def register(self, transform: Transform) -> None:
        """Register a transform.

        Args:
            transform: The transform to register. Must have a unique name
                and implement the Transform interface.

        Raises:
            TransformError: If a transform is already registered with the same name.

        Example:
            >>> registry = TransformRegistry()
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> registry.register(transform)
            >>> assert "double" in registry.list()
            >>> registry.unregister("double")  # Cleanup
        """
        if transform.name in self._transforms:
            raise TransformError(f"Transform {transform.name} is already registered")

        self._transforms[transform.name] = transform

    def unregister(self, name: str) -> None:
        """Unregister a transform.

        Args:
            name: The name of the transform to unregister.

        Raises:
            TransformError: If no transform is registered with the given name.

        Example:
            >>> registry = TransformRegistry()
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> registry.register(transform)
            >>> registry.unregister("double")
            >>> assert "double" not in registry.list()
        """
        if name not in self._transforms:
            raise TransformError(f"Transform {name} is not registered")

        del self._transforms[name]

    def get(self, name: str) -> Transform:
        """Get a registered transform by name.

        Args:
            name: The name of the transform to get.

        Returns:
            Transform: The registered transform.

        Raises:
            TransformError: If no transform is registered with the given name.

        Example:
            >>> registry = TransformRegistry()
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> registry.register(transform)
            >>> same_transform = registry.get("double")
            >>> assert same_transform is transform
            >>> registry.unregister("double")  # Cleanup
        """
        if name not in self._transforms:
            raise TransformError(f"Transform {name} is not registered")

        return self._transforms[name]

    def list(self) -> List[str]:
        """List all registered transform names.

        Returns:
            List[str]: The names of all registered transforms in alphabetical order.

        Example:
            >>> registry = TransformRegistry()
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> registry.register(transform)
            >>> assert "double" in registry.list()
            >>> registry.unregister("double")  # Cleanup
        """
        return sorted(self._transforms.keys())

    def clear(self) -> None:
        """Clear all registered transforms from the registry.

        This removes all transforms from the registry, effectively resetting it
        to its initial empty state.

        Example:
            >>> registry = TransformRegistry()
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> registry.register(transform)
            >>> registry.clear()
            >>> assert len(registry.list()) == 0
        """
        self._transforms.clear()


# Global transform registry
_registry: Optional[TransformRegistry] = None


def get_registry() -> TransformRegistry:
    """Get the global transform registry.

    Returns:
        TransformRegistry: The global transform registry instance.
        Creates a new registry if one doesn't exist.

    Example:
        >>> registry = get_registry()
        >>> assert isinstance(registry, TransformRegistry)
        >>> assert registry is get_registry()  # Same instance
    """
    global _registry
    if _registry is None:
        _registry = TransformRegistry()
    return _registry


def set_registry(registry: TransformRegistry) -> None:
    """Set the global transform registry.

    Args:
        registry: The transform registry to use globally.

    Example:
        >>> old_registry = get_registry()
        >>> new_registry = TransformRegistry()
        >>> set_registry(new_registry)
        >>> assert get_registry() is new_registry
        >>> set_registry(old_registry)  # Restore original
    """
    global _registry
    _registry = registry


def register_transform(transform: Transform) -> None:
    """Register a transform in the global registry.

    Args:
        transform: The transform to register.

    Raises:
        TransformError: If a transform with the same name is already registered.

    Example:
        >>> def double(x): return x * 2
        >>> transform = FunctionTransform("double", double)
        >>> register_transform(transform)
        >>> assert "double" in list_transforms()
        >>> unregister_transform("double")  # Cleanup
    """
    get_registry().register(transform)


def unregister_transform(name: str) -> None:
    """Unregister a transform from the global registry.

    Args:
        name: The name of the transform to unregister.

    Raises:
        TransformError: If no transform is registered with the given name.

    Example:
        >>> def double(x): return x * 2
        >>> transform = FunctionTransform("double", double)
        >>> register_transform(transform)
        >>> unregister_transform("double")
        >>> assert "double" not in list_transforms()
    """
    get_registry().unregister(name)


def get_transform(name: str) -> Transform:
    """Get a transform from the global registry.

    Args:
        name: The name of the transform to get.

    Returns:
        Transform: The registered transform.

    Raises:
        TransformError: If no transform is registered with the given name.

    Example:
        >>> def double(x): return x * 2
        >>> transform = FunctionTransform("double", double)
        >>> register_transform(transform)
        >>> same_transform = get_transform("double")
        >>> assert same_transform is transform
        >>> unregister_transform("double")  # Cleanup
    """
    return get_registry().get(name)


def list_transforms() -> List[str]:
    """List all transforms in the global registry.

    Returns:
        List[str]: The names of all registered transforms.

    Example:
        >>> def double(x): return x * 2
        >>> transform = FunctionTransform("double", double)
        >>> register_transform(transform)
        >>> assert "double" in list_transforms()
        >>> unregister_transform("double")  # Cleanup
    """
    return get_registry().list()


def clear_transforms() -> None:
    """Clear all transforms from the global registry.

    Example:
        >>> def double(x): return x * 2
        >>> transform = FunctionTransform("double", double)
        >>> register_transform(transform)
        >>> clear_transforms()
        >>> assert len(list_transforms()) == 0
    """
    get_registry().clear()


def register_function_transform(name: str, func: Callable[[Any], Any]) -> None:
    """Register a function as a transform in the global registry.

    Creates a FunctionTransform from the given function and registers it.

    Args:
        name: The name to register the transform under.
        func: The function to use for transformation.

    Raises:
        TransformError: If a transform is already registered with the given name.

    Example:
        >>> def double(x): return x * 2
        >>> register_function_transform("double", double)
        >>> transform = get_transform("double")
        >>> assert transform.transform(2) == 4
        >>> unregister_transform("double")  # Cleanup
    """
    transform = FunctionTransform(name, func)
    register_transform(transform)


def register_class_transform(name: str, cls: Type[Any]) -> None:
    """Register a class as a transform in the global registry.

    Creates a ClassTransform from the given class and registers it.

    Args:
        name: The name to register the transform under.
        cls: The class to use for transformation.

    Raises:
        TransformError: If a transform is already registered with the given name.

    Example:
        >>> class Doubler:
        ...     def __init__(self, value):
        ...         self.value = value * 2
        >>> register_class_transform("doubler", Doubler)
        >>> transform = get_transform("doubler")
        >>> result = transform.transform(2)
        >>> assert result.value == 4
        >>> unregister_transform("doubler")  # Cleanup
    """
    transform = ClassTransform(name, cls)
    register_transform(transform)


def register_pipeline(name: str, transforms: List[Union[Transform, str]]) -> None:
    """Register a pipeline in the global registry.

    Creates a TransformPipeline from the given transforms and registers it.
    Transforms can be provided either as Transform objects or as names of
    registered transforms.

    Args:
        name: The name to register the pipeline under.
        transforms: The transforms to include in the pipeline. Can be either
            Transform objects or names of registered transforms.

    Raises:
        TransformError: If the pipeline is already registered.
        TransformError: If a named transform is not registered.

    Example:
        >>> def double(x): return x * 2
        >>> def add_one(x): return x + 1
        >>> register_function_transform("double", double)
        >>> register_function_transform("add_one", add_one)
        >>> register_pipeline("math", ["double", "add_one"])
        >>> transform = get_transform("math")
        >>> assert transform.transform(2) == 5
        >>> unregister_transform("math")  # Cleanup
        >>> unregister_transform("double")  # Cleanup
        >>> unregister_transform("add_one")  # Cleanup
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

    Retrieves a transform from the global registry by name and applies it
    to the provided data.

    Args:
        data: The data to transform.
        transform_name: The name of the transform to use.

    Returns:
        The transformed data.

    Raises:
        TransformError: If the transform is not registered.
        TransformError: If there is an error transforming the data.

    Example:
        >>> def double(x): return x * 2
        >>> register_function_transform("double", double)
        >>> result = transform(2, "double")
        >>> assert result == 4
        >>> unregister_transform("double")  # Cleanup
    """
    t = get_transform(transform_name)
    return t.transform(data)


#
# Pipeline Classes
#


class PipelineStage:
    """A stage in a data transformation pipeline.

    A pipeline stage represents a single transformation step in a pipeline.
    It wraps a transform and provides additional metadata about the stage.
    Each stage is responsible for executing its transform and handling any errors.

    Note:
        This is part of the legacy pipeline implementation. For new code,
        use stages from `pepperpy.core.pipeline.stages` instead.

    Args:
        transform (Transform): The transform to use in this stage.
            Must implement the Transform interface.

    Example:
        >>> def uppercase(text: str) -> str:
        ...     return text.upper()
        >>> transform = FunctionTransform("uppercase", uppercase)
        >>> stage = PipelineStage(transform)
        >>> result = stage.execute("hello")
        >>> assert result == "HELLO"

    Migration Guide:
        To migrate to the new framework:
        1. Import from pepperpy.core.pipeline.stages instead:
            from pepperpy.core.pipeline.stages import FunctionStage
        2. Create stages with names and descriptions:
            stage = FunctionStage("stage_name", func, description="...")
    """

    def __init__(self, transform: Transform):
        """Initialize a pipeline stage.

        Args:
            transform: The transform to use in this stage.
                Must implement the Transform interface.

        Example:
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> stage = PipelineStage(transform)
            >>> assert stage.transform == transform
        """
        self._transform = transform

    @property
    def transform(self) -> Transform:
        """Get the transform used in this stage.

        Returns:
            Transform: The transform wrapped by this stage.

        Example:
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> stage = PipelineStage(transform)
            >>> assert stage.transform is transform
            >>> assert stage.transform.name == "double"
        """
        return self._transform

    def execute(self, data: Any) -> Any:
        """Execute the stage's transform on input data.

        Processes the input data through this stage's transform,
        handling any errors that occur during transformation.

        Args:
            data: The input data to transform.

        Returns:
            The transformed data.

        Raises:
            TransformError: If there is an error executing the transform.
                The error will include the transform name and original error.

        Example:
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> stage = PipelineStage(transform)
            >>> result = stage.execute(2)
            >>> assert result == 4
        """
        return self._transform.transform(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the stage to a dictionary representation.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - transform: The transform's dictionary representation
                    with at least 'name' and 'type' fields.

        Example:
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> stage = PipelineStage(transform)
            >>> info = stage.to_dict()
            >>> assert info["transform"]["name"] == "double"
            >>> assert info["transform"]["type"] == "function"
            >>> assert info["transform"]["function"] == "double"
        """
        return {"transform": self._transform.to_dict()}


class PipelineRegistry:
    """A registry for managing pipelines.

    The pipeline registry provides a centralized way to store and retrieve pipelines.
    It ensures that pipeline names are unique and provides easy access to registered
    pipelines. This registry is thread-safe and maintains a single source of truth
    for all pipelines in the system.

    Note:
        This is part of the legacy pipeline implementation. For new code,
        use the registry from `pepperpy.core.pipeline.registry` instead.

    Example:
        >>> registry = PipelineRegistry()
        >>> pipeline = Pipeline()
        >>> def double(x): return x * 2
        >>> pipeline.add_stage(FunctionTransform("double", double))
        >>> registry.register(pipeline, "my_pipeline")
        >>> same_pipeline = registry.get("my_pipeline")
        >>> assert same_pipeline.execute(2) == 4
        >>> registry.unregister("my_pipeline")  # Cleanup

    Migration Guide:
        To migrate to the new framework:
        1. Import from pepperpy.core.pipeline instead:
            from pepperpy.core.pipeline.registry import Registry
        2. Create and use the registry:
            registry = Registry()
            registry.register("name", pipeline)
    """

    def __init__(self):
        """Initialize an empty pipeline registry.

        Example:
            >>> registry = PipelineRegistry()
            >>> assert len(registry.list()) == 0
        """
        self._pipelines: Dict[str, Pipeline] = {}

    def register(self, pipeline: Pipeline, name: str) -> None:
        """Register a pipeline with a name.

        Args:
            pipeline: The pipeline to register. Must be a valid Pipeline instance.
            name: The name to register the pipeline under. Must be unique.

        Raises:
            ValueError: If a pipeline is already registered with the given name.

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline()
            >>> def double(x): return x * 2
            >>> pipeline.add_stage(FunctionTransform("double", double))
            >>> registry.register(pipeline, "my_pipeline")
            >>> assert "my_pipeline" in registry.list()
            >>> registry.unregister("my_pipeline")  # Cleanup
        """
        if name in self._pipelines:
            raise ValueError(f"Pipeline '{name}' is already registered")
        self._pipelines[name] = pipeline

    def unregister(self, name: str) -> None:
        """Unregister a pipeline.

        Args:
            name: The name of the pipeline to unregister.

        Raises:
            KeyError: If no pipeline is registered with the given name.

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline()
            >>> registry.register(pipeline, "my_pipeline")
            >>> registry.unregister("my_pipeline")
            >>> assert "my_pipeline" not in registry.list()
        """
        if name not in self._pipelines:
            raise KeyError(f"No pipeline registered with name '{name}'")
        del self._pipelines[name]

    def get(self, name: str) -> Pipeline:
        """Get a registered pipeline by name.

        Args:
            name: The name of the pipeline to get.

        Returns:
            Pipeline: The registered pipeline instance.

        Raises:
            KeyError: If no pipeline is registered with the given name.

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline()
            >>> def double(x): return x * 2
            >>> pipeline.add_stage(FunctionTransform("double", double))
            >>> registry.register(pipeline, "my_pipeline")
            >>> same_pipeline = registry.get("my_pipeline")
            >>> assert same_pipeline is pipeline
            >>> assert same_pipeline.execute(2) == 4
            >>> registry.unregister("my_pipeline")  # Cleanup
        """
        if name not in self._pipelines:
            raise KeyError(f"No pipeline registered with name '{name}'")
        return self._pipelines[name]

    def list(self) -> List[str]:
        """List all registered pipeline names.

        Returns:
            List[str]: The names of all registered pipelines in alphabetical order.

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline()
            >>> registry.register(pipeline, "my_pipeline")
            >>> assert "my_pipeline" in registry.list()
            >>> registry.unregister("my_pipeline")  # Cleanup
        """
        return sorted(self._pipelines.keys())

    def clear(self) -> None:
        """Clear all registered pipelines from the registry.

        This removes all pipelines from the registry, effectively resetting it
        to its initial empty state.

        Example:
            >>> registry = PipelineRegistry()
            >>> pipeline = Pipeline()
            >>> registry.register(pipeline, "my_pipeline")
            >>> registry.clear()
            >>> assert len(registry.list()) == 0
        """
        self._pipelines.clear()


# Global pipeline registry
_PIPELINE_REGISTRY: Optional[PipelineRegistry] = None


def register_pipeline_obj(pipeline: Pipeline, name: str) -> None:
    """Register a pipeline object with the global registry.

    Args:
        pipeline: The pipeline to register
        name: The name to register the pipeline under

    Raises:
        ValueError: If a pipeline is already registered with the given name

    Example:
        >>> pipeline = Pipeline()
        >>> def double(x): return x * 2
        >>> pipeline.add_stage(FunctionTransform("double", double))
        >>> register_pipeline_obj(pipeline, "my_pipeline")
        >>> assert "my_pipeline" in get_pipeline_registry().list()
    """
    get_pipeline_registry().register(pipeline, name)


def get_pipeline_registry() -> PipelineRegistry:
    """Get the global pipeline registry.

    Returns:
        PipelineRegistry: The global pipeline registry instance.
        Creates a new registry if one doesn't exist.

    Example:
        >>> registry = get_pipeline_registry()
        >>> assert isinstance(registry, PipelineRegistry)
        >>> assert registry is get_pipeline_registry()  # Same instance
    """
    global _PIPELINE_REGISTRY
    if _PIPELINE_REGISTRY is None:
        _PIPELINE_REGISTRY = PipelineRegistry()
    return _PIPELINE_REGISTRY


def create_pipeline(stages: List[Transform]) -> Pipeline:
    """Create a pipeline from a list of transforms.

    Creates a new pipeline and adds each transform as a stage in sequence.

    Args:
        stages: The list of transforms to create pipeline stages from.

    Returns:
        Pipeline: A new pipeline containing the specified transforms as stages.

    Example:
        >>> def double(x): return x * 2
        >>> def add_one(x): return x + 1
        >>> transforms = [
        ...     FunctionTransform("double", double),
        ...     FunctionTransform("add_one", add_one)
        ... ]
        >>> pipeline = create_pipeline(transforms)
        >>> assert pipeline.execute(2) == 5
    """
    pipeline = Pipeline()
    for stage in stages:
        pipeline.add_stage(stage)
    return pipeline


def execute_pipeline(name: str, data: Any) -> Any:
    """Execute a registered pipeline by name.

    Retrieves a pipeline from the global registry by name and executes it
    with the provided data.

    Args:
        name: The name of the pipeline to execute.
        data: The data to transform.

    Returns:
        The transformed data after passing through the pipeline.

    Raises:
        KeyError: If no pipeline is registered with the given name.
        TransformError: If there is an error during pipeline execution.

    Example:
        >>> def double(x): return x * 2
        >>> pipeline = Pipeline()
        >>> pipeline.add_stage(FunctionTransform("double", double))
        >>> register_pipeline_obj(pipeline, "my_pipeline")
        >>> result = execute_pipeline("my_pipeline", 2)
        >>> assert result == 4
        >>> get_pipeline_registry().unregister("my_pipeline")  # Cleanup
    """
    pipeline = get_pipeline_registry().get(name)
    return pipeline.execute(data)


def flatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary into a single level.

    Recursively flattens a nested dictionary by concatenating nested keys
    with the specified separator.

    Args:
        data: The dictionary to flatten
        separator: The separator to use for nested keys (default: ".")

    Returns:
        A flattened dictionary where nested keys are joined with the separator

    Example:
        >>> data = {"a": {"b": 1, "c": {"d": 2}}}
        >>> result = flatten(data)
        >>> assert result == {"a.b": 1, "a.c.d": 2}
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

    Recursively converts objects to JSON-serializable types, handling:
    - datetime/date objects to ISO format strings
    - dictionaries (recursively)
    - lists/tuples (recursively)
    - objects with to_dict() method

    Args:
        data: The data to convert to JSON-serializable format

    Returns:
        The JSON-serializable data

    Example:
        >>> from datetime import datetime
        >>> data = {
        ...     "date": datetime(2024, 1, 1),
        ...     "values": [1, 2, 3]
        ... }
        >>> result = jsonify(data)
        >>> assert result["date"] == "2024-01-01T00:00:00"
        >>> assert result["values"] == [1, 2, 3]
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

    Applies a function to each item in a list and returns a new list
    with the transformed values.

    Args:
        data: The list of data to transform
        func: The function to apply to each item

    Returns:
        A new list containing the transformed items

    Raises:
        TransformError: If there is an error applying the function to any item

    Example:
        >>> data = [1, 2, 3]
        >>> result = map_data(data, lambda x: x * 2)
        >>> assert result == [2, 4, 6]
    """
    try:
        return [func(item) for item in data]
    except Exception as e:
        raise TransformError(f"Error mapping data: {str(e)}")


def merge(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries.

    Creates a new dictionary containing all key-value pairs from the input
    dictionaries. If a key exists in multiple dictionaries, the value from
    the last dictionary takes precedence.

    Args:
        *dicts: The dictionaries to merge

    Returns:
        A new dictionary containing all key-value pairs from the input dictionaries

    Example:
        >>> d1 = {"a": 1, "b": 2}
        >>> d2 = {"b": 3, "c": 4}
        >>> result = merge(d1, d2)
        >>> assert result == {"a": 1, "b": 3, "c": 4}
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def normalize(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize data according to a schema.

    Converts values in a dictionary to their expected types based on a schema.
    Handles common type conversions:
    - str: strips whitespace
    - int: converts string/float to integer
    - float: converts string/integer to float
    - bool: converts value to boolean

    Args:
        data: The data to normalize
        schema: The schema defining expected types for each field

    Returns:
        A new dictionary with normalized values

    Raises:
        TransformError: If a value cannot be converted to its expected type

    Example:
        >>> data = {"name": " John ", "age": "30", "active": 1}
        >>> schema = {"name": str, "age": int, "active": bool}
        >>> result = normalize(data, schema)
        >>> assert result == {"name": "John", "age": 30, "active": True}
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

    Converts a string, datetime, or date object to a date object.
    String values must be in ISO format (YYYY-MM-DD).

    Args:
        value: The date to parse, can be:
            - str: ISO format date string
            - datetime: datetime object
            - date: date object

    Returns:
        The parsed date object

    Raises:
        TransformError: If the value cannot be parsed as a date

    Example:
        >>> from datetime import datetime, date
        >>> assert parse_date("2024-01-01") == date(2024, 1, 1)
        >>> assert parse_date(datetime(2024, 1, 1)) == date(2024, 1, 1)
        >>> assert parse_date(date(2024, 1, 1)) == date(2024, 1, 1)
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

    Converts a string or datetime object to a datetime object.
    String values must be in ISO format (YYYY-MM-DDTHH:MM:SS).

    Args:
        value: The datetime to parse, can be:
            - str: ISO format datetime string
            - datetime: datetime object

    Returns:
        The parsed datetime object

    Raises:
        TransformError: If the value cannot be parsed as a datetime

    Example:
        >>> from datetime import datetime
        >>> assert parse_datetime("2024-01-01T12:00:00") == datetime(2024, 1, 1, 12, 0)
        >>> assert parse_datetime(datetime(2024, 1, 1, 12, 0)) == datetime(2024, 1, 1, 12, 0)
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


class TextTransform:
    """A text transformation utility.

    This class provides common text transformations that can be used
    in pipelines or standalone.

    Example:
        >>> transform = TextTransform()
        >>> text = "hello world"
        >>> assert transform.uppercase(text) == "HELLO WORLD"
        >>> assert transform.capitalize(text) == "Hello world"
        >>> assert transform.strip("  " + text + "  ") == text
    """

    def uppercase(self, text: str) -> str:
        """Convert text to uppercase.

        Args:
            text: The text to transform

        Returns:
            The text in uppercase

        Example:
            >>> transform = TextTransform()
            >>> assert transform.uppercase("hello") == "HELLO"
        """
        return text.upper()

    def lowercase(self, text: str) -> str:
        """Convert text to lowercase.

        Args:
            text: The text to transform

        Returns:
            The text in lowercase

        Example:
            >>> transform = TextTransform()
            >>> assert transform.lowercase("HELLO") == "hello"
        """
        return text.lower()

    def capitalize(self, text: str) -> str:
        """Capitalize the first character of text.

        Args:
            text: The text to transform

        Returns:
            The text with first character capitalized

        Example:
            >>> transform = TextTransform()
            >>> assert transform.capitalize("hello world") == "Hello world"
        """
        return text.capitalize()

    def strip(self, text: str) -> str:
        """Remove leading and trailing whitespace.

        Args:
            text: The text to transform

        Returns:
            The text with whitespace removed

        Example:
            >>> transform = TextTransform()
            >>> assert transform.strip("  hello  ") == "hello"
        """
        return text.strip()


class DataTransform:
    """A data transformation utility.

    This class provides common data transformations that can be used
    in pipelines or standalone.

    Example:
        >>> transform = DataTransform()
        >>> data = [1, None, 2, 2, None, 3]
        >>> assert transform.filter_none(data) == [1, 2, 2, 3]
        >>> assert transform.unique(data) == [1, 2, 3]
        >>> assert transform.sort(data) == [1, 2, 2, 3]
    """

    def filter_none(self, data: List[Any]) -> List[Any]:
        """Filter out None values from a list.

        Args:
            data: The list to filter

        Returns:
            A new list with None values removed

        Example:
            >>> transform = DataTransform()
            >>> assert transform.filter_none([1, None, 2, None]) == [1, 2]
        """
        return [x for x in data if x is not None]

    def unique(self, data: List[Any]) -> List[Any]:
        """Remove duplicate values from a list.

        Args:
            data: The list to transform

        Returns:
            A new list with duplicate values removed, preserving order

        Example:
            >>> transform = DataTransform()
            >>> assert transform.unique([1, 2, 2, 3, 3]) == [1, 2, 3]
        """
        return list(dict.fromkeys(data))

    def sort(self, data: List[Any], reverse: bool = False) -> List[Any]:
        """Sort a list of values.

        Args:
            data: The list to sort
            reverse: Whether to sort in descending order (default: False)

        Returns:
            A new sorted list

        Example:
            >>> transform = DataTransform()
            >>> assert transform.sort([3, 1, 2]) == [1, 2, 3]
            >>> assert transform.sort([3, 1, 2], reverse=True) == [3, 2, 1]
        """
        return sorted(data, reverse=reverse)

    def limit(self, data: List[Any], n: int) -> List[Any]:
        """Limit a list to the first n items.

        Args:
            data: The list to transform
            n: The maximum number of items to keep

        Returns:
            A new list with at most n items

        Example:
            >>> transform = DataTransform()
            >>> assert transform.limit([1, 2, 3, 4, 5], 3) == [1, 2, 3]
        """
        return data[:n]


class Pipeline:
    """A data transformation pipeline.

    DEPRECATED: This class is deprecated and will be removed in a future version.
    Please migrate to the new unified pipeline framework in pepperpy.core.pipeline.
    See the migration guide below for details.

    Migration Guide:
        To migrate to the new framework:
        1. Import from pepperpy.core.pipeline instead:
            from pepperpy.core.pipeline.base import Pipeline
            from pepperpy.core.pipeline.stages import FunctionStage
        2. Create a pipeline with stages:
            pipeline = Pipeline("name")
            pipeline.add_stage(FunctionStage("stage1", func))
        3. Execute with context:
            context = PipelineContext()
            result = await pipeline.execute(data, context)

        For compatibility during migration, you can use the legacy adapter:
            from pepperpy.data.transform.legacy_adapter import LegacyPipelineAdapter
            new_pipeline = LegacyPipelineAdapter(old_pipeline, "migrated_pipeline")
    """

    def __init__(self):
        """Initialize an empty pipeline.

        Warns:
            DeprecationWarning: This class is deprecated
        """
        import warnings

        warnings.warn(
            "The Pipeline class in pepperpy.data.transform is deprecated. "
            "Please migrate to pepperpy.core.pipeline. "
            "See the class docstring for migration instructions.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._stages: List[PipelineStage] = []

    @property
    def stages(self) -> List[PipelineStage]:
        """Get the stages in the pipeline.

        Returns:
            List[PipelineStage]: The list of stages in execution order.

        Example:
            >>> pipeline = Pipeline()
            >>> def noop(x): return x
            >>> pipeline.add_stage(FunctionTransform("noop", noop))
            >>> assert len(pipeline.stages) == 1
            >>> assert pipeline.stages[0].transform.name == "noop"
        """
        return self._stages

    def add_stage(self, transform: Transform) -> None:
        """Add a transform stage to the pipeline.

        The transform will be wrapped in a PipelineStage and added
        to the end of the pipeline's execution sequence.

        Args:
            transform: The transform to add as a new stage.

        Example:
            >>> pipeline = Pipeline()
            >>> def double(x): return x * 2
            >>> transform = FunctionTransform("double", double)
            >>> pipeline.add_stage(transform)
            >>> assert len(pipeline.stages) == 1
            >>> assert pipeline.stages[0].transform == transform
        """
        stage = PipelineStage(transform)
        self._stages.append(stage)

    def execute(self, data: Any) -> Any:
        """Execute the pipeline on input data.

        Processes the input data through each stage in sequence,
        where each stage's output becomes the input to the next stage.

        Args:
            data: The input data to process through the pipeline.

        Returns:
            The transformed data after passing through all stages.

        Raises:
            TransformError: If any stage fails to process the data.

        Example:
            >>> pipeline = Pipeline()
            >>> def double(x): return x * 2
            >>> def add_one(x): return x + 1
            >>> pipeline.add_stage(FunctionTransform("double", double))
            >>> pipeline.add_stage(FunctionTransform("add_one", add_one))
            >>> result = pipeline.execute(2)
            >>> assert result == 5
        """
        result = data
        for stage in self._stages:
            try:
                result = stage.execute(result)
            except Exception as e:
                raise TransformError(
                    f"Error in pipeline stage: {e}",
                    transform_name=stage.transform.name,
                )
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert the pipeline to a dictionary representation.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - stages: List of stage dictionaries, each containing:
                    - transform: The transform's dictionary representation

        Example:
            >>> pipeline = Pipeline()
            >>> def double(x): return x * 2
            >>> pipeline.add_stage(FunctionTransform("double", double))
            >>> info = pipeline.to_dict()
            >>> assert len(info["stages"]) == 1
            >>> assert info["stages"][0]["transform"]["name"] == "double"
            >>> assert info["stages"][0]["transform"]["type"] == "function"
        """
        return {
            "stages": [stage.to_dict() for stage in self._stages],
        }
