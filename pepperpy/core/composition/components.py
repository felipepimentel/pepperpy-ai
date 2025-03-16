"""Components for composition module."""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

# Type variables with variance
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
U_co = TypeVar("U_co", covariant=True)

# Regular type variables for methods
T = TypeVar("T")
U = TypeVar("U")


class Source(Protocol[T_co]):
    """Protocol for data sources."""

    @abstractmethod
    async def get_data(self, metadata: Optional[Dict[str, Any]] = None) -> T_co:
        """Get data from the source.

        Args:
            metadata: Optional metadata

        Returns:
            Source data
        """
        pass


class Processor(Protocol[T_contra, U_co]):
    """Protocol for data processors."""

    @abstractmethod
    async def process_data(
        self,
        input_data: T_contra,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> U_co:
        """Process input data.

        Args:
            input_data: Input data to process
            metadata: Optional metadata

        Returns:
            Processed data
        """
        pass


class Output(Protocol[T_contra]):
    """Protocol for data outputs."""

    @abstractmethod
    async def write_data(
        self,
        output_data: T_contra,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write data to the output.

        Args:
            output_data: Data to write
            metadata: Optional metadata
        """
        pass


class Sources:
    """Collection of source components."""

    @staticmethod
    def from_value(value: T) -> Source[T]:
        """Create a source from a static value.

        Args:
            value: Value to use as source

        Returns:
            Source component that returns the value
        """

        class ValueSource(Source[T]):
            async def get_data(self, metadata: Optional[Dict[str, Any]] = None) -> T:
                return value

        return ValueSource()

    @staticmethod
    def from_function(func: Any) -> Source[Any]:
        """Create a source from a function.

        Args:
            func: Function to use as source

        Returns:
            Source component
        """

        class FunctionSource(Source[Any]):
            async def get_data(self, metadata: Optional[Dict[str, Any]] = None) -> Any:
                return await func(metadata) if metadata else await func()

        return FunctionSource()


class Processors:
    """Collection of processor components."""

    @staticmethod
    def from_function(func: Any) -> Processor[Any, Any]:
        """Create a processor from a function.

        Args:
            func: Function to use as processor

        Returns:
            Processor component
        """

        class FunctionProcessor(Processor[Any, Any]):
            async def process_data(
                self,
                input_data: Any,
                metadata: Optional[Dict[str, Any]] = None,
            ) -> Any:
                return (
                    await func(input_data, metadata)
                    if metadata
                    else await func(input_data)
                )

        return FunctionProcessor()


class Outputs:
    """Collection of output components."""

    @staticmethod
    def to_list() -> Output[Any]:
        """Create an output that collects values in a list.

        Returns:
            Output component
        """
        values: List[Any] = []

        class ListOutput(Output[Any]):
            async def write_data(
                self,
                output_data: Any,
                metadata: Optional[Dict[str, Any]] = None,
            ) -> None:
                values.append(output_data)

            def get_values(self) -> List[Any]:
                return values

        return ListOutput()

    @staticmethod
    def to_function(func: Any) -> Output[Any]:
        """Create an output from a function.

        Args:
            func: Function to use as output

        Returns:
            Output component
        """

        class FunctionOutput(Output[Any]):
            async def write_data(
                self,
                output_data: Any,
                metadata: Optional[Dict[str, Any]] = None,
            ) -> None:
                await func(output_data, metadata) if metadata else await func(
                    output_data
                )

        return FunctionOutput()


# Export all classes
__all__ = [
    "Source",
    "Processor",
    "Output",
    "Sources",
    "Processors",
    "Outputs",
]
