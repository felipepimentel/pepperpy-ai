"""Data processing pipeline for PepperPy.

This module implements the pipeline system for data processing,
providing:

- Pipeline definition
  - Processing steps
  - Data flows
  - Transformations
  - Validations

- Execution of pipelines
  - Asynchronous processing
  - Parallelization
  - Monitoring
  - Error handling

- Extensibility
  - Plugable components
  - Custom hooks
  - Middleware
  - Metrics

The pipeline system is fundamental for:
- Structured data processing
- Chain transformations
- Component integration
- Operation traceability
"""

from typing import Dict, List, Optional, Union

from pepperpy.pipeline.composition_adapters import (
    ComposablePipeline,
    ParallelPipeline,
    compose,
    compose_parallel,
)

__version__ = "0.1.0"
__all__ = [
    "ComposablePipeline",
    "ParallelPipeline",
    "compose",
    "compose_parallel",
]
