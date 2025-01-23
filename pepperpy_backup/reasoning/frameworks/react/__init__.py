"""ReAct reasoning framework.

This module implements the ReAct (Reasoning + Acting) framework, which
combines reasoning with action execution for dynamic problem-solving.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError


class ReActError(PepperpyError):
    """ReAct error."""
    pass


@dataclass
class ReActStep:
    """ReAct reasoning step."""
    
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


from .react_agent import ReActAgent

__all__ = [
    "ReActError",
    "ReActStep",
    "ReActAgent",
] 