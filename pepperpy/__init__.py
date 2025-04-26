"""
PepperPy - A comprehensive framework for building AI/LLM applications.

This module provides the main interfaces for working with the PepperPy framework.
"""

import sys

# Python version check
if sys.version_info < (3, 12):
    raise RuntimeError("PepperPy requires Python 3.12 or higher")

from pepperpy.content import ContentProcessor
from pepperpy.llm import LLMProvider
from pepperpy.pepperpy import PepperPy

# Import orchestration components at the end to avoid circular imports
from pepperpy.orchestration import OrchestrationProvider, WorkflowOrchestrator
from pepperpy.plugin.discovery import PluginDiscoveryProvider
from pepperpy.plugin.registry import PluginRegistry, list_plugins
from pepperpy.storage import StorageProvider

__all__ = [
    "ContentProcessor",
    "LLMProvider",
    "OrchestrationProvider",
    "PepperPy",
    "PluginDiscoveryProvider",
    "PluginRegistry",
    "StorageProvider",
    "WorkflowOrchestrator",
    "list_plugins",
]
