"""Common type definitions for PepperPy.

This module defines common types used across the framework.
"""

from typing import Any, Dict, Union

# Basic types
Metadata = Dict[str, Any]
JsonValue = Union[str, int, float, bool, None, Dict[str, Any], list]
JsonDict = Dict[str, JsonValue]
