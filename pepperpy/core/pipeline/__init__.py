"""Pipeline module for PepperPy.

This module provides the unified pipeline framework for PepperPy,
including the base pipeline implementation, stages, and registry.

Key Components:
    - Pipeline: Base pipeline implementation
    - PipelineContext: Pipeline execution context
    - PipelineStage: Base class for pipeline stages
    - PipelineRegistry: Registry for pipeline components

Example:
    >>> from pepperpy.core.pipeline import Pipeline, PipelineContext
    >>> pipeline = Pipeline("example")
    >>> pipeline.add_stage(FunctionStage("stage1", lambda x: x.upper()))
    >>> context = PipelineContext()
    >>> result = await pipeline.execute("hello", context)
    >>> assert result == "HELLO"
"""

from pepperpy.core.pipeline.base import Pipeline, PipelineContext
from pepperpy.core.pipeline.registry import PipelineRegistry
from pepperpy.core.pipeline.stages import FunctionStage, PipelineStage

__all__ = [
    "Pipeline",
    "PipelineContext",
    "PipelineStage",
    "FunctionStage",
    "PipelineRegistry",
]
