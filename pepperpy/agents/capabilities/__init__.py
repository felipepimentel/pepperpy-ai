"""Cognitive capabilities implemented by agents.

This module provides the cognitive capabilities that can be implemented by agents,
including planning, reasoning, and research.
"""

from pepperpy.agents.capabilities.base import (
    AgentCapability,
    CapabilityManager,
    CapabilityProvider,
    CapabilityRegistry,
)

# Import specific capabilities
from pepperpy.agents.capabilities.planning import PlanningCapability
from pepperpy.agents.capabilities.reasoning import ReasoningCapability
from pepperpy.agents.capabilities.research import ResearchCapability
from pepperpy.agents.capabilities.types import CapabilityType

__version__ = "0.2.0"
__all__ = [
    "AgentCapability",
    "CapabilityManager",
    "CapabilityProvider",
    "CapabilityRegistry",
    "CapabilityType",
    "PlanningCapability",
    "ReasoningCapability",
    "ResearchCapability",
]
