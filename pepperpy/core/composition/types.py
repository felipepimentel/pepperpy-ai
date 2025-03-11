"""Types for composition module."""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union

# Type variables
T = TypeVar("T")
U = TypeVar("U")

# Basic types
CompositionInput = Union[str, Dict[str, Any], List[Any]]
CompositionOutput = Union[str, Dict[str, Any], List[Any]]


# Protocol for composable components
class Composable(Protocol[T, U]):
    """Protocol for composable components."""

    @abstractmethod
    async def process(
        self, input_data: T, metadata: Optional[Dict[str, Any]] = None
    ) -> U:
        """Process input data to produce output.

        Args:
            input_data: Input data to process
            metadata: Optional metadata

        Returns:
            Processed output
        """
        pass


# Export all types
__all__ = [
    "CompositionInput",
    "CompositionOutput",
    "Composable",
]
