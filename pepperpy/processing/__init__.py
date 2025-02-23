"""Processing system for the Pepperpy framework.

This module provides a unified processing system with:
- Processing pipeline
- Data transformers
- Validators
- Metrics collection

The processing system is designed to be:
- Modular: Easy to add new processors
- Composable: Chain processors together
- Observable: Track metrics and errors
- Extensible: Support custom processors
"""

from pepperpy.processing.pipeline import (
    ProcessingError,
    ProcessingPipeline,
    ProcessingResult,
)
from pepperpy.processing.processors import (
    AudioProcessor,
    BaseProcessor,
    ContentProcessor,
)
from pepperpy.processing.transformers import (
    BaseTransformer,
    DataTransformer,
)
from pepperpy.processing.validators import (
    BaseValidator,
    DataValidator,
    DataValidatorConfig,
)

__all__ = [
    # Pipeline
    "ProcessingPipeline",
    "ProcessingResult",
    "ProcessingError",
    # Processors
    "BaseProcessor",
    "ContentProcessor",
    "AudioProcessor",
    # Transformers
    "BaseTransformer",
    "DataTransformer",
    # Validators
    "BaseValidator",
    "DataValidator",
    "DataValidatorConfig",
]
