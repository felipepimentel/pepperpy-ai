"""Learning adapters implementation."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

from ..base.capability import BaseCapability

T = TypeVar('T', bound=BaseCapability)

class LearningAdapter(ABC):
    """Base class for learning adapters."""
    
    def __init__(self, capability: T):
        """Initialize the learning adapter."""
        self.capability = capability
    
    @abstractmethod
    async def adapt_input(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt input data for learning."""
        pass
    
    @abstractmethod
    async def adapt_output(
        self,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt output data from learning."""
        pass
    
    @abstractmethod
    async def adapt_feedback(
        self,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt feedback data for learning."""
        pass

class SimpleAdapter(LearningAdapter):
    """Simple adapter that passes data through unchanged."""
    
    async def adapt_input(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pass input data through unchanged."""
        return input_data
    
    async def adapt_output(
        self,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pass output data through unchanged."""
        return output_data
    
    async def adapt_feedback(
        self,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pass feedback data through unchanged."""
        return feedback_data

class FilterAdapter(LearningAdapter):
    """Adapter that filters data based on keys."""
    
    def __init__(
        self,
        capability: T,
        input_keys: Optional[List[str]] = None,
        output_keys: Optional[List[str]] = None,
        feedback_keys: Optional[List[str]] = None
    ):
        """Initialize the filter adapter."""
        super().__init__(capability)
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.feedback_keys = feedback_keys
    
    def _filter_dict(
        self,
        data: Dict[str, Any],
        keys: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Filter dictionary by keys."""
        if not keys:
            return data
        return {k: v for k, v in data.items() if k in keys}
    
    async def adapt_input(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter input data by keys."""
        return self._filter_dict(input_data, self.input_keys)
    
    async def adapt_output(
        self,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter output data by keys."""
        return self._filter_dict(output_data, self.output_keys)
    
    async def adapt_feedback(
        self,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter feedback data by keys."""
        return self._filter_dict(feedback_data, self.feedback_keys) 