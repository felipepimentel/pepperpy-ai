"""Unified imports for the Pepperpy framework.

This module provides safe imports for commonly used external dependencies.
"""

from typing import Any, Optional, Tuple, Type, cast

from pepperpy.core.utils.imports import safe_import

# Pydantic imports
try:
    from pydantic import BaseModel as _BaseModel, Field as _Field

    BaseModel = _BaseModel
    Field = _Field
except ImportError:
    # Fallback implementation
    class BaseModel:
        """Base model when pydantic is not available."""
        def __init__(self, **kwargs: Any) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Field(*args: Any, **kwargs: Any) -> Any:
        """Field function when pydantic is not available."""
        return lambda x: x

__all__ = ["BaseModel", "Field"]
