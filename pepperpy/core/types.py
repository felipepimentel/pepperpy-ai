"""Core types module for Pepperpy framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class PepperpyError(Exception):
    """Base class for all Pepperpy errors."""
    pass


class PepperpyObject(Protocol):
    """Base protocol for all Pepperpy objects."""
    
    @property
    def name(self) -> str:
        """Get the name of the object."""
        ...


class DictInitializable(Protocol):
    """Protocol for objects that can be initialized from a dictionary."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DictInitializable':
        """Initialize object from dictionary."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary."""
        ...


class Validatable(Protocol):
    """Protocol for objects that can be validated."""
    
    def validate(self) -> None:
        """Validate object state."""
        ...


@dataclass
class PepperpyConfig:
    """Base configuration class for Pepperpy objects."""
    
    name: str
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.name:
            raise PepperpyError("Name cannot be empty")
        if self.parameters is not None and not isinstance(self.parameters, dict):
            raise PepperpyError("Parameters must be a dictionary")
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise PepperpyError("Metadata must be a dictionary") 