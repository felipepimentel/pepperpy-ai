"""Pepperpy - A powerful framework for building AI applications.

This module provides the core functionality for the Pepperpy framework,
including agents, workflows, content management, and more.
"""

__version__ = "0.1.0"

# Core components
from pepperpy.core.base import BaseComponent, Metadata
from pepperpy.core.client import PepperpyClient
from pepperpy.core.errors import PepperpyError
from pepperpy.core.messages import Message, Response
from pepperpy.core.prompts import PromptTemplate
from pepperpy.core.providers import BaseProvider, ProviderConfig
from pepperpy.core.types import ComponentState

__all__ = [
    "BaseComponent",
    "BaseProvider",
    "ComponentState",
    "Message",
    "Metadata",
    "PepperpyClient",
    "PepperpyError",
    "PromptTemplate",
    "ProviderConfig",
    "Response",
    "__version__",
]
