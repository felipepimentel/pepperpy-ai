"""Pepperpy: A simple and natural AI integration tool.

This package provides a simple and natural way to integrate AI capabilities
into your applications. It supports multiple providers, automatic configuration,
and fallback mechanisms.

Example:
    >>> from pepperpy import PepperpyClient
    >>>
    >>> async with PepperpyClient() as client:
    ...     response = await client.complete("Tell me a joke")
    ...     print(response)

"""

__version__ = "0.1.0"

from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import AutoConfig, PepperpyConfig, ProviderConfig
from pepperpy.core.templates.prompt import PromptTemplate
from pepperpy.hub import Hub

__all__ = [
    "AutoConfig",
    "PepperpyClient",
    "PepperpyConfig",
    "PromptTemplate",
    "ProviderConfig",
    "Hub",
]
