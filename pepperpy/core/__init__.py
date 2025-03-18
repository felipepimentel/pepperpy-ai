"""Core module for PepperPy.

This module provides the core functionality for the PepperPy framework,
including pipeline composition, intent recognition, and utilities.

Key Components:
    - Pipeline: Base pipeline implementation
    - Composition: High-level pipeline composition
    - Intent: Intent recognition and processing
    - Utils: Common utilities and helpers

Example:
    >>> from pepperpy.core.composition import compose, Sources
    >>> pipeline = compose("example")
    >>> pipeline.source(Sources.text("hello"))
    >>> await pipeline.execute()
    'hello'
"""

from pepperpy.core.composition import (
    Outputs,
    Processors,
    Sources,
    compose,
)
from pepperpy.core.intent import Intent, IntentType, recognize_intent
from pepperpy.core.pipeline.base import Pipeline, PipelineContext

__all__ = [
    # Composition
    "Sources",
    "Processors",
    "Outputs",
    "compose",
    # Intent
    "Intent",
    "IntentType",
    "recognize_intent",
    # Pipeline
    "Pipeline",
    "PipelineContext",
]
