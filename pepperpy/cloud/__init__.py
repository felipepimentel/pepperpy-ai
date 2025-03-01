"""Cloud Integration Module

This module provides integration with cloud services and platforms,
including AWS, GCP, Azure, and others.

It supports:
- Authentication and authorization
- Resource management
- Service discovery
- Data transfer and synchronization
"""

# Re-export from providers.cloud for backward compatibility
from pepperpy.cloud.base import CloudProvider, CloudProviderConfig
from pepperpy.providers.cloud import *

__all__ = [
    "CloudProvider",
    "CloudProviderConfig",
]
