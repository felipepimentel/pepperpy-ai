"""Chainable API methods for composition.

This module provides utilities for creating chainable API methods that can be
composed together to build complex operations. It builds on the fluent interface
patterns to provide a more specialized API for method composition.
"""

from functools import wraps
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union, cast

from pepperpy.core.fluent import FluentOperation
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic chainable methods
T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type
F = TypeVar("F", bound=Callable[..., Any])  # Function type


class ChainableMethod(Generic[T, R]):
    """Chainable method wrapper.

    This class wraps a method to make it chainable, allowing it to be composed
    with other methods in a pipeline.
    """

    def __init__(
        self,
        func: Callable[[T], R],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the chainable method.

        Args:
            func: The function to wrap
            name: Optional name for the method
            description: Optional description of what the method does
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self._next: Optional[ChainableMethod] = None

    def __call__(self, value: T) -> Union[R, Any]:
        """Call the method with the given value.

        Args:
            value: The input value

        Returns:
            The result of the method, or the result of the next method in the chain
        """
        result = self.func(value)
        if self._next is not None:
            return self._next(result)
        return result

    def then(self, next_method: "ChainableMethod") -> "ChainableMethod":
        """Chain this method with another method.

        Args:
            next_method: The next method in the chain

        Returns:
            The next method, for further chaining
        """
        self._next = next_method
        return next_method


def chainable(
    name: Optional[str] = None, description: Optional[str] = None
) -> Callable[[F], F]:
    """Decorator to make a method chainable.

    Args:
        name: Optional name for the method
        description: Optional description of what the method does

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function
            """
            return ChainableMethod(
                lambda x: func(x, *args, **kwargs), name=name, description=description
            )

        return cast(F, wrapper)

    return decorator


class Pipeline(Generic[T, R]):
    """Pipeline for composing chainable methods.

    This class provides a way to compose chainable methods into a pipeline
    that can be executed on input values.
    """

    def __init__(self, name: str):
        """Initialize the pipeline.

        Args:
            name: The name of the pipeline
        """
        self.name = name
        self.steps: List[ChainableMethod] = []
        self.metadata: Dict[str, Any] = {}

    def add_step(self, step: ChainableMethod) -> "Pipeline[T, R]":
        """Add a step to the pipeline.

        Args:
            step: The step to add

        Returns:
            Self for method chaining
        """
        self.steps.append(step)
        return self

    def with_metadata(self, key: str, value: Any) -> "Pipeline[T, R]":
        """Add metadata to the pipeline.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            Self for method chaining
        """
        self.metadata[key] = value
        return self

    def execute(self, input_value: T) -> R:
        """Execute the pipeline on the input value.

        Args:
            input_value: The input value

        Returns:
            The result of the pipeline

        Raises:
            PepperpyError: If the pipeline is empty
        """
        if not self.steps:
            raise PepperpyError("Pipeline is empty")

        # Build the chain of methods
        current = self.steps[0]
        for step in self.steps[1:]:
            current.then(step)

        # Execute the chain
        return current(input_value)


class ChainableOperation(FluentOperation[R], Generic[T, R]):
    """Chainable operation using fluent interface.

    This class combines the FluentOperation class with chainable methods
    to provide a more powerful and flexible way to build operations.
    """

    def __init__(self, name: str, input_value: Optional[T] = None):
        """Initialize the chainable operation.

        Args:
            name: The name of the operation
            input_value: Optional input value
        """
        super().__init__(name)
        self._input_value = input_value
        self._pipeline = Pipeline[T, R](name)

    def with_input(self, input_value: T) -> "ChainableOperation[T, R]":
        """Set the input value for the operation.

        Args:
            input_value: The input value

        Returns:
            Self for method chaining
        """
        self._input_value = input_value
        return self

    def add_step(self, step: ChainableMethod) -> "ChainableOperation[T, R]":
        """Add a step to the operation.

        Args:
            step: The step to add

        Returns:
            Self for method chaining
        """
        self._pipeline.add_step(step)
        return self

    def with_metadata(self, key: str, value: Any) -> "ChainableOperation[T, R]":
        """Add metadata to the operation.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            Self for method chaining
        """
        self._pipeline.with_metadata(key, value)
        return self

    async def execute(self) -> R:
        """Execute the operation.

        Returns:
            The result of the operation

        Raises:
            PepperpyError: If no input value is provided
        """
        if self._input_value is None:
            raise PepperpyError("No input value provided")

        return self._pipeline.execute(self._input_value)


def create_pipeline(name: str) -> Pipeline[Any, Any]:
    """Create a new pipeline.

    Args:
        name: The name of the pipeline

    Returns:
        A new pipeline instance
    """
    return Pipeline(name)


def create_chainable_operation(
    name: str, input_value: Optional[Any] = None
) -> ChainableOperation[Any, Any]:
    """Create a new chainable operation.

    Args:
        name: The name of the operation
        input_value: Optional input value

    Returns:
        A new chainable operation instance
    """
    return ChainableOperation(name, input_value)
