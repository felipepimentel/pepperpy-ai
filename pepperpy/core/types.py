"""Core type definitions.

This module provides core type definitions used throughout the project.
"""

from typing import NewType, TypeVar

# Core types
UserId = NewType("UserId", str)
ResourceId = NewType("ResourceId", str)
PluginId = NewType("PluginId", str)
WorkflowId = NewType("WorkflowId", str)
AgentId = NewType("AgentId", str)

# Generic types
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Result types
Result = TypeVar("Result")
Error = TypeVar("Error")

__all__ = [
    # Core types
    "UserId",
    "ResourceId",
    "PluginId",
    "WorkflowId",
    "AgentId",
    # Generic types
    "T",
    "K",
    "V",
    # Result types
    "Result",
    "Error",
]
