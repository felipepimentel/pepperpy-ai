"""Tree-of-Thoughts (ToT) reasoning framework.

This module implements the Tree-of-Thoughts reasoning framework, which
enables exploring multiple reasoning paths through a tree structure.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from pepperpy.core.utils.errors import PepperpyError


class ToTError(PepperpyError):
    """Tree-of-Thoughts error."""
    pass


@dataclass
class ToTNode:
    """Tree-of-Thoughts node."""
    
    thought: str
    children: Set[str] = field(default_factory=set)
    parent: Optional[str] = None
    value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


from .processor import TreeOfThoughtProcessor
from .tree_of_thoughts import TreeOfThoughtsAgent

__all__ = [
    "ToTError",
    "ToTNode",
    "TreeOfThoughtProcessor",
    "TreeOfThoughtsAgent",
]
