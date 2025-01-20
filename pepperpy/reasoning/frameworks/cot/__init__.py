"""Chain-of-Thought (CoT) reasoning framework.

This module implements the Chain-of-Thought reasoning framework, which
enables step-by-step reasoning through explicit thought processes.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError


class CoTError(PepperpyError):
    """Chain-of-Thought error."""
    pass


@dataclass
class CoTStep:
    """Chain-of-Thought reasoning step."""
    
    thought: str
    intermediate_result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


from .cot_agent import CoTAgent

__all__ = [
    "CoTError",
    "CoTStep",
    "CoTAgent",
] 