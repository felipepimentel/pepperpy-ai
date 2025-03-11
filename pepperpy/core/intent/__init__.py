"""Intent module for PepperPy.

This module provides functionality for intent recognition and handling.
"""

from pepperpy.core.intent.public import (
    Intent,
    IntentBuilder,
    IntentManager,
    IntentProvider,
    process_intent,
)

__all__ = [
    "Intent",
    "IntentBuilder",
    "IntentManager",
    "IntentProvider",
    "process_intent",
]
