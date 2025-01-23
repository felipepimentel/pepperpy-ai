"""Base profile implementation."""

import logging
from typing import Any, Dict, List, Optional, Set

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ProfileError(PepperpyError):
    """Profile error."""
    pass


class Profile(Lifecycle):
    """Agent profile implementation."""
    
    def __init__(
        self,
        name: str,
        description: str,
        goals: List[str],
        capabilities: Optional[Set[str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize profile.
        
        Args:
            name: Profile name
            description: Profile description
            goals: Profile goals
            capabilities: Optional set of capabilities
            preferences: Optional profile preferences
            constraints: Optional profile constraints
            metadata: Optional profile metadata
            config: Optional profile configuration
        """
        super().__init__(name)
        self._description = description
        self._goals = goals
        self._capabilities = capabilities or set()
        self._preferences = preferences or {}
        self._constraints = constraints or {}
        self._metadata = metadata or {}
        self._config = config or {}
        
    @property
    def description(self) -> str:
        """Return profile description."""
        return self._description
        
    @property
    def goals(self) -> List[str]:
        """Return profile goals."""
        return self._goals
        
    @property
    def capabilities(self) -> Set[str]:
        """Return profile capabilities."""
        return self._capabilities
        
    @property
    def preferences(self) -> Dict[str, Any]:
        """Return profile preferences."""
        return self._preferences
        
    @property
    def constraints(self) -> Dict[str, Any]:
        """Return profile constraints."""
        return self._constraints
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return profile metadata."""
        return self._metadata
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return profile configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize profile."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up profile."""
        pass
        
    def has_capability(self, capability: str) -> bool:
        """Check if profile has capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            True if profile has capability, False otherwise
        """
        return capability in self._capabilities
        
    def get_preference(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Any:
        """Get profile preference.
        
        Args:
            key: Preference key
            default: Optional default value
            
        Returns:
            Preference value or default
        """
        return self._preferences.get(key, default)
        
    def get_constraint(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Any:
        """Get profile constraint.
        
        Args:
            key: Constraint key
            default: Optional default value
            
        Returns:
            Constraint value or default
        """
        return self._constraints.get(key, default)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary.
        
        Returns:
            Profile as dictionary
        """
        return {
            "name": self.name,
            "description": self._description,
            "goals": self._goals,
            "capabilities": list(self._capabilities),
            "preferences": self._preferences,
            "constraints": self._constraints,
            "metadata": self._metadata,
            "config": self._config,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """Create profile from dictionary.
        
        Args:
            data: Profile data
            
        Returns:
            Profile instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            goals=data["goals"],
            capabilities=set(data.get("capabilities", [])),
            preferences=data.get("preferences"),
            constraints=data.get("constraints"),
            metadata=data.get("metadata"),
            config=data.get("config"),
        )
        
    def validate(self) -> None:
        """Validate profile state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Profile name cannot be empty")
            
        if not self._description:
            raise ValueError("Profile description cannot be empty")
            
        if not self._goals:
            raise ValueError("Profile must have at least one goal") 