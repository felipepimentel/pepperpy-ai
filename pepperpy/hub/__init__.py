"""PepperHub integration capabilities.

This module provides interfaces and implementations for working with
PepperHub, including asset management, sharing, and collaboration.

Example:
    >>> from pepperpy.hub import HubProvider
    >>> provider = HubProvider.from_config({
    ...     "provider": "local",
    ...     "storage": "memory"
    ... })
    >>> asset = await provider.create_asset(
    ...     name="my_prompt",
    ...     content="You are a helpful assistant.",
    ...     type="prompt"
    ... )
    >>> await provider.publish_asset(asset.id)
"""

from pepperpy.hub.base import (
    Asset,
    AssetStatus,
    AssetType,
    AssetVersion,
    HubError,
    HubProvider,
)
from pepperpy.hub.local import LocalHubProvider

__all__ = [
    "Asset",
    "AssetStatus",
    "AssetType",
    "AssetVersion",
    "HubError",
    "HubProvider",
    "LocalHubProvider",
]
