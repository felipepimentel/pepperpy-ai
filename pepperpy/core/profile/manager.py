"""Profile manager implementation.

This module provides functionality for managing multiple AI profiles,
including profile creation, retrieval, and persistence.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.errors import PepperpyError
from ..providers.base import BaseProvider
from ..core.events import Event, EventBus
from ..monitoring import Monitor
from .profile import Profile


class ManagerError(PepperpyError):
    """Manager error."""
    pass


class ProfileManager(BaseProvider):
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
        self._event_bus = event_bus
        self._monitor = monitor
        self._profiles: Dict[str, Profile] = {}
        self._lock = asyncio.Lock()
        super().__init__(name, config)
        
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
            ManagerError: If profile creation fails
        """
        async with self._lock:
            if id in self._profiles:
                raise ManagerError(f"Profile {id} already exists")
                
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
                                "profile_name": name,
                            },
                        )
                    )
                    
                return profile
                
            except Exception as e:
                raise ManagerError(f"Failed to create profile: {e}")
                
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
            raise ManagerError(f"Profile {id} not found")
            
        return self._profiles[id]
        
    async def delete_profile(self, id: str) -> None:
        """Delete profile.
        
        Args:
            id: Profile ID
            
        Raises:
            ManagerError: If profile deletion fails
        """
        async with self._lock:
            if id not in self._profiles:
                raise ManagerError(f"Profile {id} not found")
                
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
                            data={
                                "profile_id": id,
                            },
                        )
                    )
                    
            except Exception as e:
                raise ManagerError(f"Failed to delete profile: {e}")
                
    def list_profiles(self) -> List[str]:
        """List profiles.
        
        Returns:
            List of profile IDs
        """
        return list(self._profiles.keys())
        
    async def _initialize_impl(self) -> None:
        """Initialize manager."""
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
    async def _cleanup_impl(self) -> None:
        """Clean up manager."""
        try:
            for profile in self._profiles.values():
                await profile.cleanup()
                
            self._profiles.clear()
            
            if self._monitor:
                await self._monitor.cleanup()
                
            if self._event_bus:
                await self._event_bus.cleanup()
                
        except Exception as e:
            raise ManagerError(f"Failed to clean up manager: {e}")
            
    def _validate_impl(self) -> None:
        """Validate manager state."""
        if not self.name:
            raise ManagerError("Empty manager name") 