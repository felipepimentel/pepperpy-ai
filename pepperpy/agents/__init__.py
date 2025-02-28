"""Agent module for PepperPy.

Implements different types of agents and their capabilities,
enabling autonomous and interactive task execution.
"""

from typing import Dict, List, Optional, Union

__version__ = "0.1.0"

# Import providers subpackage
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

# Note: These imports are commented out as they could not be resolved
# Uncomment when these modules are implemented
"""
from .multi_agent import (
    Agent,
    AgentRole,
    CollaborationSystem,
    Consensus,
    Message,
    Task,
    TeamFormation,
)
from .planning import (
    Plan,
    PlanExecutor,
    PlanManager,
    Planner,
    PlanStatus,
    PlanStep,
)
from .reasoning import (
    Belief,
    BeliefSystem,
    Conclusion,
    Explanation,
    LogicalReasoner,
    Premise,
    ReasoningEngine,
    ReasoningStrategy,
)
"""

__all__ = [
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
    # The following are commented out as they could not be resolved
    # Uncomment when these modules are implemented
    """
    # Planning
    "PlanStatus",
    "PlanStep",
    "Plan",
    "Planner",
    "PlanExecutor",
    "PlanManager",
    # Reasoning
    "ReasoningStrategy",
    "Premise",
    "Conclusion",
    "LogicalReasoner",
    "Belief",
    "BeliefSystem",
    "ReasoningEngine",
    "Explanation",
    # Multi-agent
    "AgentRole",
    "Message",
    "Task",
    "Agent",
    "CollaborationSystem",
    "TeamFormation",
    "Consensus",
    """,
]
