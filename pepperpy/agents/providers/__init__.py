"""Providers package for the Pepperpy framework.

This package provides implementations of various AI model providers and
services that can be used by agents. The providers are organized by
their service type and capabilities.
"""

from pepperpy.agents.providers.base import BaseProvider
from pepperpy.agents.providers.domain import (
    ProviderCapability,
    ProviderConfig,
    ProviderContext,
    ProviderMetadata,
    ProviderState,
)
from pepperpy.agents.providers.engine import ProviderEngine
from pepperpy.agents.providers.factory import ProviderFactory
from pepperpy.agents.providers.manager import ProviderManager
from pepperpy.agents.providers.types import (
    ProviderID,
    ProviderMessage,
    ProviderResponse,
)

__version__ = "0.1.0"

__all__ = [
    # Base
    "BaseProvider",
    # Domain
    "ProviderCapability",
    "ProviderConfig",
    "ProviderContext",
    "ProviderMetadata",
    "ProviderState",
    # Engine
    "ProviderEngine",
    # Factory
    "ProviderFactory",
    # Manager
    "ProviderManager",
    # Types
    "ProviderID",
    "ProviderMessage",
    "ProviderResponse",
]
