"""Diagnostics module for PepperPy.

This module provides tools and utilities for diagnosing and optimizing PepperPy
components, including profiling, visualization, and optimization suggestions.
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.core.diagnostics.analyzer import PipelineAnalyzer
from pepperpy.core.diagnostics.optimizer import Optimizer
from pepperpy.core.diagnostics.profiler import Profiler
from pepperpy.core.diagnostics.visualizer import Visualizer

__all__ = [
    "PipelineAnalyzer",
    "Profiler",
    "Visualizer",
    "Optimizer",
    "analyze_pipeline",
    "profile_execution",
    "visualize_pipeline",
    "suggest_optimizations",
]


def analyze_pipeline(pipeline: Any, **kwargs: Any) -> "PipelineAnalyzer":
    """Analyze a pipeline for potential issues and optimizations.

    Args:
        pipeline: The pipeline to analyze
        **kwargs: Additional parameters for analysis

    Returns:
        A PipelineAnalyzer instance with analysis results

    Examples:
        >>> import pepperpy as pp
        >>> pipeline = pp.Pipeline.builder().add(pp.llm.generate()).build()
        >>> analysis = pp.analyze_pipeline(pipeline)
        >>> print(analysis.summary())
    """
    analyzer = PipelineAnalyzer(pipeline)
    analyzer.analyze(**kwargs)
    return analyzer


def profile_execution(
    component: Any,
    inputs: Dict[str, Any],
    **kwargs: Any,
) -> "Profiler":
    """Profile the execution of a component or pipeline.

    Args:
        component: The component or pipeline to profile
        inputs: The inputs to the component
        **kwargs: Additional parameters for profiling

    Returns:
        A Profiler instance with profiling results

    Examples:
        >>> import pepperpy as pp
        >>> pipeline = pp.Pipeline.builder().add(pp.llm.generate()).build()
        >>> profiler = pp.profile_execution(pipeline, {"prompt": "Hello, world!"})
        >>> print(profiler.summary())
    """
    profiler = Profiler()
    profiler.profile(component, inputs, **kwargs)
    return profiler


def visualize_pipeline(
    pipeline: Any,
    format: str = "svg",
    **kwargs: Any,
) -> Union[str, bytes]:
    """Visualize a pipeline as a diagram.

    Args:
        pipeline: The pipeline to visualize
        format: The output format (svg, png, dot)
        **kwargs: Additional parameters for visualization

    Returns:
        The visualization in the requested format

    Examples:
        >>> import pepperpy as pp
        >>> pipeline = pp.Pipeline.builder().add(pp.llm.generate()).build()
        >>> svg = pp.visualize_pipeline(pipeline)
        >>> with open("pipeline.svg", "w") as f:
        ...     f.write(svg)
    """
    visualizer = Visualizer()
    return visualizer.visualize(pipeline, format=format, **kwargs)


def suggest_optimizations(
    component: Any,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Suggest optimizations for a component or pipeline.

    Args:
        component: The component or pipeline to optimize
        **kwargs: Additional parameters for optimization

    Returns:
        A list of optimization suggestions

    Examples:
        >>> import pepperpy as pp
        >>> pipeline = pp.Pipeline.builder().add(pp.llm.generate()).build()
        >>> suggestions = pp.suggest_optimizations(pipeline)
        >>> for suggestion in suggestions:
        ...     print(f"{suggestion['name']}: {suggestion['description']}")
    """
    optimizer = Optimizer()
    return optimizer.suggest(component, **kwargs)
