"""Decision module for managing decision making.

This module provides functionality for making decisions based on various
strategies and criteria, including validation and composition.
"""

from .criteria import (
    CriteriaError,
    DecisionCriteria,
    CompositeCriteria,
)
from .strategy import (
    StrategyError,
    DecisionStrategy,
    CompositeStrategy,
)
from .decision_maker import (
    DecisionError,
    Decision,
    DecisionMaker,
)

__all__ = [
    "CriteriaError",
    "DecisionCriteria",
    "CompositeCriteria",
    "StrategyError",
    "DecisionStrategy",
    "CompositeStrategy",
    "DecisionError",
    "Decision",
    "DecisionMaker",
]
