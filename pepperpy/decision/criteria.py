"""Decision criteria implementation.

This module provides functionality for defining and evaluating decision
criteria, including validation and composition.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pepperpy.common.errors import PepperpyError


class CriteriaError(PepperpyError):
    """Criteria error."""
    pass


class DecisionCriteria(ABC):
    """Decision criteria interface."""
    
    def __init__(self, name: str) -> None:
        """Initialize criteria.
        
        Args:
            name: Criteria name
        """
        self.name = name
        
    @abstractmethod
    def is_satisfied(self, context: Dict[str, Any]) -> bool:
        """Check if criteria is satisfied.
        
        Args:
            context: Decision context
            
        Returns:
            True if satisfied, False otherwise
        """
        pass
        
    def validate(self) -> None:
        """Validate criteria state."""
        if not self.name:
            raise CriteriaError("Empty criteria name")
            
    def __str__(self) -> str:
        """Get string representation.
        
        Returns:
            String representation
        """
        return f"DecisionCriteria({self.name})"


class CompositeCriteria(DecisionCriteria):
    """Composite decision criteria."""
    
    def __init__(
        self,
        name: str,
        criteria: List[DecisionCriteria],
        require_all: bool = True,
    ) -> None:
        """Initialize criteria.
        
        Args:
            name: Criteria name
            criteria: Child criteria
            require_all: Whether all criteria must be satisfied
        """
        super().__init__(name)
        self._criteria = criteria
        self._require_all = require_all
        
    def is_satisfied(self, context: Dict[str, Any]) -> bool:
        """Check if criteria is satisfied.
        
        Args:
            context: Decision context
            
        Returns:
            True if satisfied, False otherwise
        """
        if not self._criteria:
            return True
            
        if self._require_all:
            return all(c.is_satisfied(context) for c in self._criteria)
        else:
            return any(c.is_satisfied(context) for c in self._criteria)
            
    def validate(self) -> None:
        """Validate criteria state."""
        super().validate()
        
        for criterion in self._criteria:
            criterion.validate() 