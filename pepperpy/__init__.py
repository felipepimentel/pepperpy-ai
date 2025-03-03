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

# Providers are now distributed by domain
# The following imports are for backward compatibility
from pepperpy.agents.providers import *
from pepperpy.cloud.providers import *
from pepperpy.core import *
from pepperpy.core.config.providers import *
from pepperpy.embedding.providers import *
from pepperpy.llm.providers import *
from pepperpy.memory.providers import *
from pepperpy.multimodal.audio.providers import *
from pepperpy.multimodal.vision.providers import *
from pepperpy.storage.providers import *

# from pepperpy.integrations import *  # noqa
# from pepperpy.utils import *  # noqa


# The centralized providers module has been removed
# Please use the domain-specific providers instead
# For example: from pepperpy.llm.providers import OpenAIProvider

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
