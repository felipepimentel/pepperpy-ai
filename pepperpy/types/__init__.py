"""PepperPy Types Module.

This module provides type-related functionality for the PepperPy framework, including:
- Common type definitions for use throughout the framework
- Utilities for type checking and manipulation
- Reflection and introspection utilities

The types module is designed to provide a common set of types and utilities
for working with types in a consistent way across the framework.
"""

import os
from pathlib import Path
from typing import Union

from pepperpy.types.common import (
    Context as Context,
)
from pepperpy.types.common import (
    Document as Document,
)
from pepperpy.types.common import (
    Identifiable as Identifiable,
)
from pepperpy.types.common import (
    Metadata as Metadata,
)
from pepperpy.types.common import (
    Result as Result,
)
from pepperpy.types.common import (
    VectorEmbedding as VectorEmbedding,
)
from pepperpy.types.public import *

# Type for path-like objects
PathLike = Union[str, Path, os.PathLike]

# Export all types
__all__ = ["PathLike"]
