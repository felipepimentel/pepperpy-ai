"""Event handler functionality.

This module provides functionality for handling events, including
filtering, transformation, and validation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from .types import Event, EventFilter, EventTransformer, EventValidator


class HandlerError(PepperpyError):
    """Handler error."""
    pass


class EventHandler(Lifecycle, ABC):
    """Base class for event handlers."""
    
    def __init__(self, name: str):
        """Initialize handler.
        
        Args:
            name: Handler name
        """
        super().__init__()
        self.name = name
        self._filters: List[EventFilter] = []
        self._transformers: List[EventTransformer] = []
        self._validators: List[EventValidator] = []
        
    def add_filter(self, filter_: EventFilter) -> None:
        """Add event filter.
        
        Args:
            filter_: Filter to add
        """
        self._filters.append(filter_)
        
    def add_transformer(self, transformer: EventTransformer) -> None:
        """Add event transformer.
        
        Args:
            transformer: Transformer to add
        """
        self._transformers.append(transformer)
        
    def add_validator(self, validator: EventValidator) -> None:
        """Add event validator.
        
        Args:
            validator: Validator to add
        """
        self._validators.append(validator)
        
    def _filter_event(self, event: Event) -> bool:
        """Filter event through all filters.
        
        Args:
            event: Event to filter
            
        Returns:
            True if event passes all filters, False otherwise
        """
        return all(f.matches(event) for f in self._filters)
        
    def _transform_event(self, event: Event) -> Event:
        """Transform event through all transformers.
        
        Args:
            event: Event to transform
            
        Returns:
            Transformed event
        """
        for transformer in self._transformers:
            event = transformer.transform(event)
        return event
        
    def _validate_event(self, event: Event) -> bool:
        """Validate event through all validators.
        
        Args:
            event: Event to validate
            
        Returns:
            True if event passes all validators, False otherwise
        """
        return all(v.validate(event) for v in self._validators)
        
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle event.
        
        Args:
            event: Event to handle
            
        Raises:
            HandlerError: If handling fails
        """
        if not self._filter_event(event):
            return
            
        event = self._transform_event(event)
        
        if not self._validate_event(event):
            raise HandlerError(f"Event validation failed: {event}")
        
    def validate(self) -> None:
        """Validate handler state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Handler name cannot be empty")
