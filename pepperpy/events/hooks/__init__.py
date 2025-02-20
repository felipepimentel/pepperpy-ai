"""Hooks system for the Pepperpy framework.

This module provides the hook system that allows extending and customizing
the framework's behavior through callbacks and event handlers.
"""

from pepperpy.events.hooks.base import (
    HookCallback,
    HookManager,
    hook_manager,
)

__all__ = [
    "HookCallback",
    "HookManager",
    "hook_manager",
]
