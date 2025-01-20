"""Pepperpy: A modular and extensible framework for scalable AI systems."""

from importlib import metadata

try:
    __version__ = metadata.version("pepperpy")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

from . import (
    agents,
    common,
    context,
    data,
    decision,
    events,
    learning,
    lifecycle,
    memory,
    monitoring,
    orchestrator,
    profile,
    reasoning,
    runtime,
    security,
    tools,
)

__all__ = [
    "agents",
    "common",
    "context",
    "data",
    "decision",
    "events",
    "learning",
    "lifecycle",
    "memory",
    "monitoring",
    "orchestrator",
    "profile",
    "reasoning",
    "runtime",
    "security",
    "tools",
]
