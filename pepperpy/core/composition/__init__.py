"""Composition module for PepperPy.

This module provides functionality for composing components into pipelines.
"""

from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.composition.components import (
    Output,
    Outputs,
    Processor,
    Processors,
    Source,
    Sources,
)
from pepperpy.core.errors import PepperPyError

# Type variables
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


async def compose(
    source: Source[T],
    processor: Processor[T, U],
    output: Output[U],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Compose a source, processor, and output into a pipeline.

    Args:
        source: Data source
        processor: Data processor
        output: Data output
        metadata: Optional metadata

    Raises:
        PepperPyError: If composition fails
    """
    try:
        # Get data from source
        input_data = await source.get_data(metadata)

        # Process data
        processed_data = await processor.process_data(input_data, metadata)

        # Write to output
        await output.write_data(processed_data, metadata)

    except Exception as e:
        raise PepperPyError(f"Error in composition: {e}")


async def compose_parallel(
    sources: List[Source[T]],
    processor: Processor[List[T], U],
    output: Output[U],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Compose multiple sources in parallel with a processor and output.

    Args:
        sources: List of data sources
        processor: Data processor
        output: Data output
        metadata: Optional metadata

    Raises:
        PepperPyError: If composition fails
    """
    try:
        # Get data from all sources
        input_data = []
        for source in sources:
            data = await source.get_data(metadata)
            input_data.append(data)

        # Process data
        processed_data = await processor.process_data(input_data, metadata)

        # Write to output
        await output.write_data(processed_data, metadata)

    except Exception as e:
        raise PepperPyError(f"Error in parallel composition: {e}")


__all__ = [
    # Components
    "Source",
    "Processor",
    "Output",
    "Sources",
    "Processors",
    "Outputs",
    # Composition
    "compose",
    "compose_parallel",
]
