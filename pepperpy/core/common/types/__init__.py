"""Core types for the PepperPy framework"""

# Import basic types
from typing import Any, Dict, List, Optional, Tuple, Union

# Define common type aliases
PathLike = Union[str, bytes]
JsonDict = Dict[str, Any]
JsonList = List[Any]

__all__ = [
    "PathLike",
    "JsonDict",
    "JsonList",
]
