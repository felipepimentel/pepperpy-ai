"""Composition module for PepperPy.

This module provides functionality for composing components into pipelines.
"""

from pepperpy.core.composition.components import (
    Output,
    Outputs,
    Processor,
    Processors,
    Source,
    Sources,
)
from pepperpy.core.composition.public import (
    compose,
    compose_parallel,
)

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
