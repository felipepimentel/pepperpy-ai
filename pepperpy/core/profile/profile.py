"""Profile implementation.

This module provides functionality for managing AI profiles,
including preferences, settings, and history tracking.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import logging

from ..core.events import Event, EventBus
from ..interfaces import BaseProvider
from ..common.errors import PepperpyError
from ..monitoring import Monitor


class ProfileError(PepperpyError):
    """Profile error."""
    pass


class Profile(BaseProvider):
    """Profile class."""
    
    def __init__(
        self,
        id: str,
        name: str,
        event_bus: Optional[EventBus] = None,
        monitor: Optional[Monitor] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize profile.
        
        Args:
            id: Profile ID
            name: Profile name
            event_bus: Optional event bus
            monitor: Optional monitor
            config: Optional configuration
        """
        self._id = id
        self._event_bus = event_bus
        self._monitor = monitor
        self._preferences: Dict[str, Any] = {}
        self._settings: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        super().__init__(name, config)
        
    @property
    def id(self) -> str:
        """Get profile ID."""
        return self._id
        
    @property
    def preferences(self) -> Dict[str, Any]:
        """Get preferences."""
        return self._preferences.copy()
        
    @property
    def settings(self) -> Dict[str, Any]:
        """Get settings."""
        return self._settings.copy()
        
    async def set_preference(self, key: str, value: Any) -> None:
        """Set preference.
        
        Args:
            key: Preference key
            value: Preference value
            
        Raises:
            ProfileError: If preference cannot be set
        """
        if not key:
            raise ProfileError("Empty preference key")
            
        self._preferences[key] = value
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="preference_changed",
                    source=self.name,
                    timestamp=datetime.now(),
                    data={
                        "profile_id": self.id,
                        "key": key,
                        "value": value,
                    },
                )
            )
            
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value
        """
        return self._preferences.get(key, default)
        
    async def set_setting(self, key: str, value: Any) -> None:
        """Set setting.
        
        Args:
            key: Setting key
            value: Setting value
            
        Raises:
            ProfileError: If setting cannot be set
        """
        if not key:
            raise ProfileError("Empty setting key")
            
        self._settings[key] = value
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="setting_changed",
                    source=self.name,
                    timestamp=datetime.now(),
                    data={
                        "profile_id": self.id,
                        "key": key,
                        "value": value,
                    },
                )
            )
            
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value
        """
        return self._settings.get(key, default)
        
    async def add_history(self, event: Dict[str, Any]) -> None:
        """Add history event.
        
        Args:
            event: History event
            
        Raises:
            ProfileError: If event cannot be added
        """
        if not event:
            raise ProfileError("Empty history event")
            
        self._history.append({
            **event,
            "timestamp": datetime.now(),
        })
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="history_added",
                    source=self.name,
                    timestamp=datetime.now(),
                    data={
                        "profile_id": self.id,
                        "event": event,
                    },
                )
            )
            
    def get_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get history events.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of history events
        """
        events = self._history.copy()
        
        if start_time:
            events = [e for e in events if e["timestamp"] >= start_time]
            
        if end_time:
            events = [e for e in events if e["timestamp"] <= end_time]
            
        return events
        
    async def clear_history(self) -> None:
        """Clear history."""
        self._history.clear()
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="history_cleared",
                    source=self.name,
                    timestamp=datetime.now(),
                    data={
                        "profile_id": self.id,
                    },
                )
            )
            
    async def _initialize_impl(self) -> None:
        """Initialize profile."""
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
    async def _cleanup_impl(self) -> None:
        """Clean up profile."""
        self._preferences.clear()
        self._settings.clear()
        self._history.clear()
        
        if self._monitor:
            await self._monitor.cleanup()
            
        if self._event_bus:
            await self._event_bus.cleanup()
            
    async def _validate_impl(self) -> None:
        """Validate profile state."""
        if not self.id:
            raise ProfileError("Empty profile ID")
            
        if not self.name:
            raise ProfileError("Empty profile name")
            
        if self._event_bus:
            await self._event_bus.validate()
            
        if self._monitor:
            await self._monitor.validate() 