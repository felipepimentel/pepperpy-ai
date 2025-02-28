"""Cloud service providers

This module implements integrations with cloud service providers,
offering:

- Resource management
  - Compute
  - Storage
  - Networking
  - Containers

- Managed services
  - Databases
  - Cache
  - Messaging
  - Analytics

- Security and identity
  - Authentication
  - Authorization

Supported providers:
- Amazon Web Services (AWS)
- Microsoft Azure
- Google Cloud Platform (GCP)
- Other providers as needed
"""

from typing import Dict, List, Optional, Union

from pepperpy.cloud.base import CloudProvider, CloudProviderConfig
from pepperpy.cloud.providers.aws import AWSProvider
from pepperpy.cloud.providers.gcp import GCPStorageProvider

__version__ = "0.1.0"
__all__ = [
    "CloudProvider",
    "CloudProviderConfig",
    "AWSProvider",
    "GCPStorageProvider",
]
