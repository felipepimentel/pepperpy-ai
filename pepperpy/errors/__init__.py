"""PepperPy Errors Module.

This module provides error classes for the PepperPy framework.
"""

from pepperpy.errors.public import *

__all__ = [
    "PeppyError",
    "ValidationError",
    "ConfigError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
]
