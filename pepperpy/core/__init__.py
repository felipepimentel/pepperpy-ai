"""Core package providing fundamental functionality for PepperPy.

This package provides core functionality and base classes used throughout
the PepperPy system.
"""

from .base import Lifecycle
from .types import ComponentState

__all__ = [
    'Lifecycle',
    'ComponentState',
]
