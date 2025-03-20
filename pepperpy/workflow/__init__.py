"""Pipeline Domain Module.

This module provides data processing pipeline capabilities for PepperPy,
including pipeline stages, registries, and execution management.

Example:
    >>> from pepperpy.pipeline import Pipeline, Stage
    >>> pipeline = Pipeline()
    >>> pipeline.add_stage(Stage("process"))
    >>> result = pipeline.execute(data)

Components:
    - Pipeline: Core pipeline execution engine
    - Stage: Individual processing stage
    - Registry: Pipeline component registry
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

from .registry import Registry

__all__ = [
    "Registry",
]

# Type variables
T = TypeVar("T")
