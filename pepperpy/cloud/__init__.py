"""Cloud Integration Module

This module provides integration with cloud services and platforms,
including AWS, GCP, Azure, and others.

It supports:
- Authentication and authorization
- Resource management
- Service discovery
- Data transfer and synchronization
"""

# Re-export public interfaces
from pepperpy.cloud.public import (
    CloudProvider,
    CloudProviderConfig,
    CloudService,
)

# Import internal implementations
from pepperpy.storage.providers.cloud import CloudStorageProvider

__all__ = [
    # Public interfaces
    "CloudProvider",
    "CloudProviderConfig",
    "CloudService",
    # Implementation classes
    "CloudStorageProvider",
]
