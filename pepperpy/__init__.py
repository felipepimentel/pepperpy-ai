"""PepperPy Framework.

A Python framework for building AI-powered applications.

Core Components:
1. Core Framework
   - Configuration management
   - Error handling
   - Lifecycle management
   - State management
   - Security

2. Processing
   - Agent management
   - Workflow orchestration
   - Content synthesis
   - Memory management

3. Integrations
   - LangChain integration
   - AutoGen integration
   - Provider management
   - Plugin system

4. Utilities
   - Common utilities
   - Helper functions
   - Shared tools
"""

from pepperpy.core.common import *  # noqa
# from pepperpy.integrations import *  # noqa
from pepperpy.processing import *  # noqa
# from pepperpy.utils import *  # noqa

__version__ = "0.1.0"

__all__ = [
    # Core components
    "Config",
    "Environment",
    "FeatureFlags",
    "ObservabilityManager",
    "SecurityManager",
    "StateManager",
    # Processing
    "AgentManager",
    "WorkflowManager",
    "SynthesisManager",
    "MemoryManager",
    # Integrations
    "LangChainIntegration",
    "AutoGenIntegration",
    "ProviderManager",
    "PluginManager",
    # Utilities
    "Timer",
    "Cache",
    "Validator",
]
