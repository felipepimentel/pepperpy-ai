"""Common type definitions for PepperPy.

This module provides common type definitions used throughout the PepperPy framework.
"""

import os
from pathlib import Path
from typing import Dict, List, TypeVar, Union

# PathLike is a type alias for various path-like objects
PathLike = Union[str, os.PathLike, Path]

# JSON type definitions
JSONPrimitive = Union[str, int, float, bool, None]
JSONValue = Union[JSONPrimitive, List["JSONValue"], Dict[str, "JSONValue"]]
JSONDict = Dict[str, JSONValue]
JSONList = List[JSONValue]

# Common type variables
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
K = TypeVar("K")
