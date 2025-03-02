"""Core base classes for PepperPy.

This module provides base classes and interfaces used throughout the PepperPy system.
"""

from .protocols.lifecycle import Lifecycle

# Re-export Lifecycle for backward compatibility
__all__ = ["Lifecycle"]
