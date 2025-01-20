"""Metrics monitor implementation."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..common.errors import PepperpyError
from .base import Monitor, MonitoringError


logger = logging.getLogger(__name__)


class MetricsMonitor(Monitor):
    """Metrics monitor implementation."""
    
    def __init__(
        self,
        name: str,
        storage: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize metrics monitor.
        
        Args:
            name: Monitor name
            storage: Optional in-memory storage
            config: Optional monitor configuration
        """
        super().__init__(name, config)
        self._storage = storage or {}
        
    @property
    def storage(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return metrics storage."""
        return self._storage
        
    async def _initialize(self) -> None:
        """Initialize metrics monitor."""
        await super()._initialize()
        
    async def _cleanup(self) -> None:
        """Clean up metrics monitor."""
        await super()._cleanup()
        self._storage.clear()
        
    async def record(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record metric event.
        
        Args:
            event_type: Event type
            data: Event data
            context: Optional event context
            
        Raises:
            MonitoringError: If recording fails
        """
        try:
            # Create event entry
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
                "context": context or {},
            }
            
            # Store event
            if event_type not in self._storage:
                self._storage[event_type] = []
                
            self._storage[event_type].append(event)
            
        except Exception as e:
            raise MonitoringError(f"Failed to record metric: {e}") from e
            
    async def query(
        self,
        event_type: str,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query metric events.
        
        Args:
            event_type: Event type
            filters: Optional event filters
            context: Optional query context
            
        Returns:
            List of matching events
            
        Raises:
            MonitoringError: If query fails
        """
        try:
            # Get events for type
            events = self._storage.get(event_type, [])
            
            # Apply filters
            if filters:
                filtered_events = []
                for event in events:
                    match = True
                    for key, value in filters.items():
                        if key not in event["data"] or event["data"][key] != value:
                            match = False
                            break
                    if match:
                        filtered_events.append(event)
                events = filtered_events
                
            return events
            
        except Exception as e:
            raise MonitoringError(f"Failed to query metrics: {e}") from e
            
    def validate(self) -> None:
        """Validate metrics monitor state."""
        super().validate()
        
        if not isinstance(self._storage, dict):
            raise ValueError("Storage must be a dictionary") 