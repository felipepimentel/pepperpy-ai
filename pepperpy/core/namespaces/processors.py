"""Processors namespace for PepperPy.

This module provides a namespace for accessing processor components.
"""

from typing import Any, Callable, Dict


class ProcessorsNamespace:
    """Namespace for processor components."""

    def __init__(self):
        """Initialize the processors namespace."""
        pass

    def transform(self, func: Callable[[Any], Any]) -> Dict[str, Any]:
        """Create a transform processor.

        Args:
            func: Function to transform the input

        Returns:
            A processor configuration
        """
        return {"type": "transform", "function": func}

    def filter(self, predicate: Callable[[Any], bool]) -> Dict[str, Any]:
        """Create a filter processor.

        Args:
            predicate: Function to filter the input

        Returns:
            A processor configuration
        """
        return {"type": "filter", "predicate": predicate}

    def map(self, func: Callable[[Any], Any]) -> Dict[str, Any]:
        """Create a map processor.

        Args:
            func: Function to map each item in the input

        Returns:
            A processor configuration
        """
        return {"type": "map", "function": func}

    def reduce(
        self, func: Callable[[Any, Any], Any], initial: Any = None
    ) -> Dict[str, Any]:
        """Create a reduce processor.

        Args:
            func: Function to reduce the input
            initial: Initial value for the reduction

        Returns:
            A processor configuration
        """
        return {"type": "reduce", "function": func, "initial": initial}

    def summarize(self, max_length: int = 100) -> Dict[str, Any]:
        """Create a summarize processor.

        Args:
            max_length: Maximum length of the summary

        Returns:
            A processor configuration
        """
        return {"type": "summarize", "max_length": max_length}


# Create a singleton instance
processors = ProcessorsNamespace()
