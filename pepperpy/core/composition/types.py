"""Types for composition module."""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union

# Type variables for composable components
# T is contravariant (input)
# U is covariant (output)
T_contra = TypeVar("T_contra", contravariant=True)
U_co = TypeVar("U_co", covariant=True)

# Basic types
CompositionInput = Union[str, Dict[str, Any], List[Any]]
CompositionOutput = Union[str, Dict[str, Any], List[Any]]


# Protocol for composable components
class Composable(Protocol[T_contra, U_co]):
    """Protocol for composable components."""

    @abstractmethod
    async def process(
        self, input_data: T_contra, metadata: Optional[Dict[str, Any]] = None
    ) -> U_co:
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
