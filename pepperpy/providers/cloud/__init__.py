"""Provider implementations for cloud capabilities.

This module provides implementations of various cloud service providers,
allowing the framework to interact with different cloud platforms.

It includes providers for:
- AWS (Amazon Web Services)
- GCP (Google Cloud Platform)
- Cloud storage services
"""

from pepperpy.providers.cloud.gcp import GCPStorageProvider

__all__ = ["GCPStorageProvider"]
