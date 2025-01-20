"""Base configuration classes for Pepperpy."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

import yaml

from ...common.types import DictInitializable, Validatable
from ...common.errors import ConfigError

T = TypeVar("T", bound="BaseConfig")

class BaseConfig(DictInitializable, Validatable, ABC):
    """Base class for all Pepperpy configurations."""
    
    @classmethod
    def load(cls: Type[T], path: Path) -> T:
        """Load configuration from YAML file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Configuration instance
            
        Raises:
            ConfigError: If file cannot be loaded or is invalid
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
                
            if not isinstance(data, dict):
                raise ConfigError(f"Invalid configuration format in {path}")
                
            return cls.from_dict(data)
            
        except Exception as e:
            raise ConfigError(f"Failed to load configuration from {path}: {str(e)}") from e
            
    def save(self, path: Path) -> None:
        """Save configuration to YAML file.
        
        Args:
            path: Output path
            
        Raises:
            ConfigError: If configuration cannot be saved
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w") as f:
                yaml.safe_dump(self.to_dict(), f, indent=2)
                
        except Exception as e:
            raise ConfigError(f"Failed to save configuration to {path}: {str(e)}") from e
            
    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create configuration from dictionary.
        
        Args:
            data: Dictionary with configuration data
            
        Returns:
            Configuration instance
            
        Raises:
            ConfigError: If dictionary is invalid
        """
        ...
        
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary with configuration data
        """
        ...
        
    @abstractmethod
    def validate(self) -> None:
        """Validate configuration state.
        
        Raises:
            ConfigError: If configuration is invalid
        """
        ...
        
    def merge(self, other: "BaseConfig") -> None:
        """Merge another configuration into this one.
        
        Args:
            other: Configuration to merge
            
        Raises:
            ConfigError: If configurations cannot be merged
        """
        if not isinstance(other, self.__class__):
            raise ConfigError(
                f"Cannot merge configuration of type {type(other)} into {type(self)}"
            )
            
        try:
            self._merge(other)
            self.validate()
            
        except Exception as e:
            raise ConfigError(f"Failed to merge configurations: {str(e)}") from e
            
    @abstractmethod
    def _merge(self, other: "BaseConfig") -> None:
        """Merge implementation to be provided by subclasses."""
        ... 