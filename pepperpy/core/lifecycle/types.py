"""Core lifecycle types module.

This module defines the core types used for lifecycle management.
"""

from enum import Enum


class LifecycleState(str, Enum):
    """Component lifecycle states."""

    UNINITIALIZED = "uninitialized"
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    FINALIZED = "finalized" 