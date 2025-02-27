"""Core types for PepperPy.

This module provides core type definitions used throughout the PepperPy system.
"""

from enum import Enum


class ComponentState(Enum):
    """State of a system component."""

    UNREGISTERED = "unregistered"
    INITIALIZING = "initializing"
    RUNNING = "running"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
