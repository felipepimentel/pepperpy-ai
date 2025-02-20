"""Pepperpy: A Python framework for building AI-powered applications.

This package provides tools and abstractions for:
- Building and running AI agents
- Managing workflows and pipelines
- Integrating with language models and tools
- Sharing and discovering artifacts via the Hub
"""

__version__ = "0.1.0"

from pepperpy.cli import cli
from pepperpy.core.errors import PepperpyError
from pepperpy.hub import (
    LocalStorageBackend,
    MarketplaceConfig,
    MarketplaceManager,
    Publisher,
    SecurityConfig,
    SecurityManager,
    StorageBackend,
    StorageMetadata,
)

__all__ = [
    # Version
    "__version__",
    # CLI
    "cli",
    # Errors
    "PepperpyError",
    # Hub
    "MarketplaceConfig",
    "MarketplaceManager",
    "Publisher",
    "SecurityConfig",
    "SecurityManager",
    "StorageBackend",
    "StorageMetadata",
    "LocalStorageBackend",
]
