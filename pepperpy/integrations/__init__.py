"""External integrations for PepperPy.

This module provides integrations with external services and libraries:

1. LangChain Integration:
   - Chain management
   - Model integration
   - Tool integration

2. AutoGen Integration:
   - Agent management
   - Multi-agent orchestration
   - Task automation

3. Provider Management:
   - Provider registration
   - Factory patterns
   - Type validation
"""

from .base import *  # noqa
from .langchain import *  # noqa
from .autogen import *  # noqa
from .registry import *  # noqa
from .types import *  # noqa

__all__ = [
    # Base components
    "Integration",
    "IntegrationProvider",
    "IntegrationConfig",
    # LangChain
    "LangChainIntegration",
    "LangChainProvider",
    "LangChainConfig",
    # AutoGen
    "AutoGenIntegration",
    "AutoGenProvider",
    "AutoGenConfig",
    # Registry
    "IntegrationRegistry",
    "register_integration",
    "get_integration",
]
