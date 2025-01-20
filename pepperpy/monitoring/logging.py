"""Logging monitor implementation."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..common.errors import PepperpyError
from .base import Monitor, MonitoringError


logger = logging.getLogger(__name__)


class LoggingMonitor(Monitor):
    """Logging monitor implementation."""
    
    def __init__(
        self,
        name: str,
        logger_name: Optional[str] = None,
        log_level: int = logging.INFO,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize logging monitor.
        
        Args:
            name: Monitor name
            logger_name: Optional logger name
            log_level: Log level (default: INFO)
            config: Optional monitor configuration
        """
        super().__init__(name, config)
        self._logger = logging.getLogger(logger_name or name)
        self._logger.setLevel(log_level)
        self._log_level = log_level
        self._logs: List[Dict[str, Any]] = []
        
    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return self._logger
        
    @property
    def log_level(self) -> int:
        """Return log level."""
        return self._log_level
        
    @property
    def logs(self) -> List[Dict[str, Any]]:
        """Return logs."""
        return self._logs
        
    async def _initialize(self) -> None:
        """Initialize logging monitor."""
        await super()._initialize()
        
    async def _cleanup(self) -> None:
        """Clean up logging monitor."""
        await super()._cleanup()
        self._logs.clear()
        
    async def record(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record log event.
        
        Args:
            event_type: Event type
            data: Event data
            context: Optional event context
            
        Raises:
            MonitoringError: If recording fails
        """
        try:
            # Create log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": event_type,
                "data": data,
                "context": context or {},
            }
            
            # Store log
            self._logs.append(log_entry)
            
            # Format log message
            message = f"{event_type}: {data}"
            if context:
                message += f" (context: {context})"
                
            # Log message
            self._logger.log(self._log_level, message)
            
        except Exception as e:
            raise MonitoringError(f"Failed to record log: {e}") from e
            
    async def query(
        self,
        event_type: str,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query log events.
        
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
            # Filter logs by type
            logs = [log for log in self._logs if log["type"] == event_type]
            
            # Apply filters
            if filters:
                filtered_logs = []
                for log in logs:
                    match = True
                    for key, value in filters.items():
                        if key not in log["data"] or log["data"][key] != value:
                            match = False
                            break
                    if match:
                        filtered_logs.append(log)
                logs = filtered_logs
                
            return logs
            
        except Exception as e:
            raise MonitoringError(f"Failed to query logs: {e}") from e
            
    def validate(self) -> None:
        """Validate logging monitor state."""
        super().validate()
        
        if not self._logger:
            raise ValueError("Logger not provided")
            
        if not isinstance(self._logs, list):
            raise ValueError("Logs must be a list") 