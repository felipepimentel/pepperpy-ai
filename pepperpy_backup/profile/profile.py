"""Profile implementation.

This module provides functionality for managing AI profiles,
including preferences, settings, and history tracking.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.events import Event, EventBus
from pepperpy.monitoring import Monitor


class ProfileError(PepperpyError):
    """Profile error."""
    pass


class Profile(Lifecycle):
    """Profile implementation."""
    
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
        super().__init__()
        self.id = id
        self.name = name
        self._event_bus = event_bus
        self._monitor = monitor
        self._config = config or {}
        self._preferences: Dict[str, Any] = {}
        self._settings: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._created_at = datetime.now()
        self._updated_at = self._created_at
        
    @property
    def preferences(self) -> Dict[str, Any]:
        """Get profile preferences.
        
        Returns:
            Profile preferences
        """
        return self._preferences.copy()
        
    async def set_preference(self, key: str, value: Any) -> None:
        """Set profile preference.
        
        Args:
            key: Preference key
            value: Preference value
            
        Raises:
            ProfileError: If preference invalid
        """
        if not key:
            raise ProfileError("Empty preference key")
            
        self._preferences[key] = value
        self._updated_at = datetime.now()
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="preference_updated",
                    source=self.name,
                    timestamp=self._updated_at,
                    data={
                        "profile_id": self.id,
                        "key": key,
                        "value": value,
                    },
                )
            )
            
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get profile preference.
        
        Args:
            key: Preference key
            default: Default value
            
        Returns:
            Preference value
        """
        return self._preferences.get(key, default)
        
    @property
    def settings(self) -> Dict[str, Any]:
        """Get profile settings.
        
        Returns:
            Profile settings
        """
        return self._settings.copy()
        
    async def set_setting(self, key: str, value: Any) -> None:
        """Set profile setting.
        
        Args:
            key: Setting key
            value: Setting value
            
        Raises:
            ProfileError: If setting invalid
        """
        if not key:
            raise ProfileError("Empty setting key")
            
        self._settings[key] = value
        self._updated_at = datetime.now()
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="setting_updated",
                    source=self.name,
                    timestamp=self._updated_at,
                    data={
                        "profile_id": self.id,
                        "key": key,
                        "value": value,
                    },
                )
            )
            
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get profile setting.
        
        Args:
            key: Setting key
            default: Default value
            
        Returns:
            Setting value
        """
        return self._settings.get(key, default)
        
    async def add_history(self, event: Dict[str, Any]) -> None:
        """Add history event.
        
        Args:
            event: History event
            
        Raises:
            ProfileError: If event invalid
        """
        if not event:
            raise ProfileError("Empty history event")
            
        event["timestamp"] = datetime.now()
        self._history.append(event)
        self._updated_at = event["timestamp"]
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="history_added",
                    source=self.name,
                    timestamp=self._updated_at,
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
        """Get profile history.
        
        Args:
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            Profile history
        """
        history = self._history
        
        if start_time:
            history = [
                e for e in history
                if e["timestamp"] >= start_time
            ]
            
        if end_time:
            history = [
                e for e in history
                if e["timestamp"] <= end_time
            ]
            
        return history
        
    async def clear_history(self) -> None:
        """Clear profile history."""
        self._history.clear()
        self._updated_at = datetime.now()
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="history_cleared",
                    source=self.name,
                    timestamp=self._updated_at,
                    data={"profile_id": self.id},
                )
            )
            
    async def _initialize(self) -> None:
        """Initialize profile."""
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
    async def _cleanup(self) -> None:
        """Clean up profile."""
        if self._monitor:
            await self._monitor.cleanup()
            
        if self._event_bus:
            await self._event_bus.cleanup()
            
    def validate(self) -> None:
        """Validate profile state."""
        super().validate()
        
        if not self.id:
            raise ProfileError("Empty profile ID")
            
        if not self.name:
            raise ProfileError("Empty profile name")
            
        if self._event_bus:
            self._event_bus.validate()
            
        if self._monitor:
            self._monitor.validate() 