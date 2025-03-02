"""Batch processing optimization for API requests.

This module provides tools for optimizing API requests through batching:
- Request grouping to reduce API calls
- Efficient scheduling of batched operations
- Dynamic batch sizing based on rate limits
- Priority-based batch processing
"""

# Import directly from the modules that were previously in the batching directory
from pepperpy.optimization.base import (
    Batch,
    BatchManager,
    BatchProcessor,
    BatchScheduler,
)

__all__ = [
    "Batch",
    "BatchProcessor",
    "BatchManager",
    "BatchScheduler",
]
