"""Profile manager implementation.

This module provides functionality for managing multiple AI profiles,
including profile creation, retrieval, and persistence.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.events import Event, EventBus
from pepperpy.monitoring import Monitor
from .profile import Profile, ProfileError


class ManagerError(PepperpyError):
    """Manager error."""
    pass


class ProfileManager(Lifecycle):
    """Profile manager implementation."""
    
    def __init__(
        self,
        name: str,
        event_bus: Optional[EventBus] = None,
        monitor: Optional[Monitor] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize manager.
        
        Args:
            name: Manager name
            event_bus: Optional event bus
            monitor: Optional monitor
            config: Optional configuration
        """
        super().__init__()
        self.name = name
        self._event_bus = event_bus
        self._monitor = monitor
        self._config = config or {}
        self._profiles: Dict[str, Profile] = {}
        self._lock = asyncio.Lock()
        
    async def create_profile(
        self,
        id: str,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Profile:
        """Create profile.
        
        Args:
            id: Profile ID
            name: Profile name
            config: Optional configuration
            
        Returns:
            Created profile
            
        Raises:
            ManagerError: If creation fails
        """
        async with self._lock:
            if id in self._profiles:
                raise ManagerError(f"Profile already exists: {id}")
                
            try:
                profile = Profile(
                    id=id,
                    name=name,
                    event_bus=self._event_bus,
                    monitor=self._monitor,
                    config=config,
                )
                await profile.initialize()
                self._profiles[id] = profile
                
                if self._event_bus:
                    await self._event_bus.publish(
                        Event(
                            type="profile_created",
                            source=self.name,
                            timestamp=datetime.now(),
                            data={
                                "profile_id": id,
                                "name": name,
                            },
                        )
                    )
                    
                return profile
            except Exception as e:
                raise ManagerError(f"Profile creation failed: {e}")
                
    async def get_profile(self, id: str) -> Profile:
        """Get profile.
        
        Args:
            id: Profile ID
            
        Returns:
            Profile instance
            
        Raises:
            ManagerError: If profile not found
        """
        if id not in self._profiles:
            raise ManagerError(f"Profile not found: {id}")
            
        return self._profiles[id]
        
    async def delete_profile(self, id: str) -> None:
        """Delete profile.
        
        Args:
            id: Profile ID
            
        Raises:
            ManagerError: If deletion fails
        """
        async with self._lock:
            if id not in self._profiles:
                raise ManagerError(f"Profile not found: {id}")
                
            try:
                profile = self._profiles[id]
                await profile.cleanup()
                del self._profiles[id]
                
                if self._event_bus:
                    await self._event_bus.publish(
                        Event(
                            type="profile_deleted",
                            source=self.name,
                            timestamp=datetime.now(),
                            data={"profile_id": id},
                        )
                    )
            except Exception as e:
                raise ManagerError(f"Profile deletion failed: {e}")
                
    def list_profiles(self) -> List[str]:
        """List profile IDs.
        
        Returns:
            List of profile IDs
        """
        return list(self._profiles.keys())
        
    async def _initialize(self) -> None:
        """Initialize manager."""
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
    async def _cleanup(self) -> None:
        """Clean up manager."""
        async with self._lock:
            for profile in self._profiles.values():
                await profile.cleanup()
                
            self._profiles.clear()
            
            if self._monitor:
                await self._monitor.cleanup()
                
            if self._event_bus:
                await self._event_bus.cleanup()
                
    def validate(self) -> None:
        """Validate manager state."""
        super().validate()
        
        if not self.name:
            raise ManagerError("Empty manager name")
            
        if self._event_bus:
            self._event_bus.validate()
            
        if self._monitor:
            self._monitor.validate()
            
        for profile in self._profiles.values():
            try:
                profile.validate()
            except Exception as e:
                raise ManagerError(f"Profile validation failed: {e}") 