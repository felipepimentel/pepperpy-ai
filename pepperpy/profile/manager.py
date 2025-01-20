"""Profile manager implementation."""

import logging
from typing import Any, Dict, List, Optional, Set

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle
from .base import Profile, ProfileError


logger = logging.getLogger(__name__)


class ProfileManager(Lifecycle):
    """Profile manager implementation."""
    
    def __init__(
        self,
        name: str,
        profiles: Optional[Dict[str, Profile]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize profile manager.
        
        Args:
            name: Profile manager name
            profiles: Optional dictionary of profiles
            config: Optional profile manager configuration
        """
        super().__init__(name)
        self._profiles = profiles or {}
        self._config = config or {}
        
    @property
    def profiles(self) -> Dict[str, Profile]:
        """Return profiles."""
        return self._profiles
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return profile manager configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize profile manager."""
        for profile in self._profiles.values():
            await profile.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up profile manager."""
        for profile in self._profiles.values():
            await profile.cleanup()
            
    def add_profile(self, profile: Profile) -> None:
        """Add profile.
        
        Args:
            profile: Profile to add
            
        Raises:
            ProfileError: If profile already exists
        """
        if profile.name in self._profiles:
            raise ProfileError(f"Profile {profile.name} already exists")
            
        self._profiles[profile.name] = profile
        
    def remove_profile(self, name: str) -> None:
        """Remove profile.
        
        Args:
            name: Profile name
            
        Raises:
            ProfileError: If profile does not exist
        """
        if name not in self._profiles:
            raise ProfileError(f"Profile {name} does not exist")
            
        del self._profiles[name]
        
    def get_profile(self, name: str) -> Profile:
        """Get profile.
        
        Args:
            name: Profile name
            
        Returns:
            Profile instance
            
        Raises:
            ProfileError: If profile does not exist
        """
        if name not in self._profiles:
            raise ProfileError(f"Profile {name} does not exist")
            
        return self._profiles[name]
        
    def has_profile(self, name: str) -> bool:
        """Check if profile exists.
        
        Args:
            name: Profile name
            
        Returns:
            True if profile exists, False otherwise
        """
        return name in self._profiles
        
    def get_profiles_with_capability(self, capability: str) -> List[Profile]:
        """Get profiles with capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            List of profiles with capability
        """
        return [
            profile for profile in self._profiles.values()
            if profile.has_capability(capability)
        ]
        
    def get_profiles_with_goal(self, goal: str) -> List[Profile]:
        """Get profiles with goal.
        
        Args:
            goal: Goal to check
            
        Returns:
            List of profiles with goal
        """
        return [
            profile for profile in self._profiles.values()
            if goal in profile.goals
        ]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile manager to dictionary.
        
        Returns:
            Profile manager as dictionary
        """
        return {
            "name": self.name,
            "profiles": {
                name: profile.to_dict()
                for name, profile in self._profiles.items()
            },
            "config": self._config,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileManager":
        """Create profile manager from dictionary.
        
        Args:
            data: Profile manager data
            
        Returns:
            Profile manager instance
        """
        profiles = {
            name: Profile.from_dict(profile_data)
            for name, profile_data in data.get("profiles", {}).items()
        }
        
        return cls(
            name=data["name"],
            profiles=profiles,
            config=data.get("config"),
        )
        
    def validate(self) -> None:
        """Validate profile manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Profile manager name cannot be empty")
            
        for profile in self._profiles.values():
            profile.validate() 