"""
PepperPy Framework.

A Python framework for building plugin-based applications.
"""

# Version information
__version__ = "0.1.0"

# Core framework
# Logging
from .core.logging import get_logger

# Factory functions
from .factory import (
    create_agent,
    create_content,
    create_embeddings,
    create_llm,
    create_plugin,
    create_rag,
    create_storage,
    create_tts,
    create_workflow,
)
from .pepperpy import (
    # Type definitions
    DependencyType,
    EventPriority,
    # Core API
    PepperPy,
    ResourceType,
    ServiceScope,
    cleanup_plugins,
    # Event system
    event,
    get_pepperpy,
    init_framework,
    # Lifecycle management
    initialize_plugins,
    # Dependency injection
    inject,
    # Plugin system
    plugin,
    publish_event,
    service,
)

# Plugin API
from .plugins.plugin import PepperpyPlugin
from .plugins.registry import get_plugin
