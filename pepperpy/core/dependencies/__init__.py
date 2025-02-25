"""Dependency management system.

This module provides dependency management functionality:
- Dependency resolution and tracking
- Dependency validation and lifecycle
- Dependency providers and injection
"""

from pepperpy.core.dependencies.manager import DependencyManager

# Export public API
__all__ = [
    "DependencyManager",
]
