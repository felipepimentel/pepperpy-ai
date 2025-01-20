"""Base monitoring implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class MonitoringError(PepperpyError):
    """Monitoring error."""
    pass


class Monitor(Lifecycle, ABC):
    """Monitor implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize monitor.
        
        Args:
            name: Monitor name
            config: Optional monitor configuration
        """
        super().__init__(name)
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return monitor configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize monitor."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up monitor."""
        pass
        
    @abstractmethod
    async def record(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record monitoring event.
        
        Args:
            event_type: Event type
            data: Event data
            context: Optional event context
        """
        pass
        
    @abstractmethod
    async def query(
        self,
        event_type: str,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query monitoring events.
        
        Args:
            event_type: Event type
            filters: Optional event filters
            context: Optional query context
            
        Returns:
            List of matching events
        """
        pass
        
    def validate(self) -> None:
        """Validate monitor state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Monitor name cannot be empty") 