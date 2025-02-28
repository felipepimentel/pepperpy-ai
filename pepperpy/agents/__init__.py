"""Agent module for PepperPy.

Implements different types of agents and their capabilities,
enabling autonomous and interactive task execution.
"""

from typing import Dict, List, Optional, Union

__version__ = "0.1.0"

# Import implementations subpackage
from .implementations import (
    AutonomousAgent,
    AutonomousAgentConfig,
    InteractiveAgent,
    InteractiveAgentConfig,
    WorkflowAgent,
    WorkflowAgentConfig,
)

# Import workflows subpackage
from .workflows import (
    BaseWorkflow,
    WorkflowCallback,
    WorkflowConfig,
    WorkflowDefinition,
    WorkflowPriority,
    WorkflowRegistry,
    WorkflowStatus,
    WorkflowStep,
)

from .providers import (
    BaseProvider,
    ProviderCapability,
    ProviderConfig,
    ProviderContext,
    ProviderEngine,
    ProviderFactory,
    ProviderID,
    ProviderManager,
    ProviderMessage,
    ProviderMetadata,
    ProviderResponse,
    ProviderState,
)

__all__ = [
    # Implementations
    "AutonomousAgent",
    "AutonomousAgentConfig",
    "InteractiveAgent",
    "InteractiveAgentConfig",
    "WorkflowAgent",
    "WorkflowAgentConfig",
    # Workflows
    "BaseWorkflow",
    "WorkflowCallback",
    "WorkflowConfig",
    "WorkflowDefinition",
    "WorkflowPriority",
    "WorkflowRegistry",
    "WorkflowStatus",
    "WorkflowStep",
    # Providers
    "BaseProvider",
    "ProviderCapability",
    "ProviderConfig",
    "ProviderContext",
    "ProviderEngine",
    "ProviderFactory",
    "ProviderManager",
    "ProviderMetadata",
    "ProviderState",
    "ProviderID",
    "ProviderMessage",
    "ProviderResponse",
]
