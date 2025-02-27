"""Módulo de agentes do PepperPy

Implementa diferentes tipos de agentes e suas capacidades,
permitindo a execução de tarefas autônomas e interativas.
"""

from typing import Dict, List, Optional, Union

__version__ = "0.1.0"
__all__ = []  # Will be populated as implementations are added

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

__all__ = [
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
]
