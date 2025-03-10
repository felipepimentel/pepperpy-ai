"""Core functionality for data transformation.

This module provides the core functionality for data transformation,
including transformers and pipelines.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Type, TypeVar, Union

from pepperpy.data.errors import TransformError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for data types
T = TypeVar("T")
U = TypeVar("U")


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
        result = data

        for transform in self._transforms:
            try:
                result = transform.transform(result)
            except TransformError as e:
                raise TransformError(
                    f"Error in pipeline at transform '{transform.name}': {e}",
                    transform_name=self.name,
                )
            except Exception as e:
                raise TransformError(
                    f"Error in pipeline at transform '{transform.name}': {e}",
                    transform_name=self.name,
                )

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary.

        Returns:
            The transform as a dictionary
        """
        return {
            "name": self.name,
            "type": self.transform_type.value,
            "transforms": [transform.to_dict() for transform in self._transforms],
        }


class TransformRegistry:
    """Registry for transforms.

    The transform registry is responsible for managing transforms.
    """

    def __init__(self):
        """Initialize a transform registry."""
        self._transforms: Dict[str, Transform] = {}

    def register(self, transform: Transform) -> None:
        """Register a transform.

        Args:
            transform: The transform to register

        Raises:
            TransformError: If a transform with the same name is already registered
        """
        if transform.name in self._transforms:
            raise TransformError(f"Transform '{transform.name}' is already registered")

        self._transforms[transform.name] = transform

    def unregister(self, name: str) -> None:
        """Unregister a transform.

        Args:
            name: The name of the transform to unregister

        Raises:
            TransformError: If the transform is not registered
        """
        if name not in self._transforms:
            raise TransformError(f"Transform '{name}' is not registered")

        del self._transforms[name]

    def get(self, name: str) -> Transform:
        """Get a transform by name.

        Args:
            name: The name of the transform

        Returns:
            The transform

        Raises:
            TransformError: If the transform is not registered
        """
        if name not in self._transforms:
            raise TransformError(f"Transform '{name}' is not registered")

        return self._transforms[name]

    def list(self) -> List[str]:
        """List all registered transforms.

        Returns:
            The names of all registered transforms
        """
        return list(self._transforms.keys())

    def clear(self) -> None:
        """Clear all registered transforms."""
        self._transforms.clear()


# Default transform registry
_registry = TransformRegistry()


def get_registry() -> TransformRegistry:
    """Get the default transform registry.

    Returns:
        The default transform registry
    """
    return _registry


def set_registry(registry: TransformRegistry) -> None:
    """Set the default transform registry.

    Args:
        registry: The transform registry to set as the default
    """
    global _registry
    _registry = registry


def register_transform(transform: Transform) -> None:
    """Register a transform in the default registry.

    Args:
        transform: The transform to register

    Raises:
        TransformError: If a transform with the same name is already registered
    """
    get_registry().register(transform)


def unregister_transform(name: str) -> None:
    """Unregister a transform from the default registry.

    Args:
        name: The name of the transform to unregister

    Raises:
        TransformError: If the transform is not registered
    """
    get_registry().unregister(name)


def get_transform(name: str) -> Transform:
    """Get a transform by name from the default registry.

    Args:
        name: The name of the transform

    Returns:
        The transform

    Raises:
        TransformError: If the transform is not registered
    """
    return get_registry().get(name)


def list_transforms() -> List[str]:
    """List all registered transforms in the default registry.

    Returns:
        The names of all registered transforms
    """
    return get_registry().list()


def clear_transforms() -> None:
    """Clear all registered transforms in the default registry."""
    get_registry().clear()


def register_function_transform(name: str, func: Callable[[Any], Any]) -> None:
    """Register a function as a transform.

    Args:
        name: The name of the transform
        func: The function to register

    Raises:
        TransformError: If a transform with the same name is already registered
    """
    transform = FunctionTransform(name, func)
    register_transform(transform)


def register_class_transform(name: str, cls: Type[Any]) -> None:
    """Register a class as a transform.

    Args:
        name: The name of the transform
        cls: The class to register

    Raises:
        TransformError: If a transform with the same name is already registered
    """
    transform = ClassTransform(name, cls)
    register_transform(transform)


def register_pipeline(name: str, transforms: List[Union[Transform, str]]) -> None:
    """Register a pipeline of transforms.

    Args:
        name: The name of the pipeline
        transforms: The transforms to apply, either as Transform objects or names of registered transforms

    Raises:
        TransformError: If a transform with the same name is already registered
        TransformError: If a transform name is not registered
    """
    # Resolve transform names to Transform objects
    resolved_transforms = []

    for transform in transforms:
        if isinstance(transform, str):
            resolved_transforms.append(get_transform(transform))
        else:
            resolved_transforms.append(transform)

    pipeline = TransformPipeline(name, resolved_transforms)
    register_transform(pipeline)


def transform(data: Any, transform_name: str) -> Any:
    """Transform data using a registered transform.

    Args:
        data: The data to transform
        transform_name: The name of the transform

    Returns:
        The transformed data

    Raises:
        TransformError: If the transform is not registered
        TransformError: If there is an error transforming the data
    """
    transform_obj = get_transform(transform_name)
    return transform_obj.transform(data)
