"""Base configuration classes and utilities."""

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints

import yaml

from pepperpy.common.errors import PepperpyError


class ConfigError(PepperpyError):
    """Error raised for configuration-related issues."""
    pass


T = TypeVar("T", bound="BaseConfig")


@dataclass
class BaseConfig:
    """Base configuration class with common functionality."""
    
    config_path: Optional[Path] = None
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_types()
        self.validate()
    
    def _validate_types(self) -> None:
        """Validate field types match type hints.
        
        Raises:
            ConfigError: If type validation fails.
        """
        type_hints = get_type_hints(self.__class__)
        for field in fields(self):
            value = getattr(self, field.name)
            if value is not None:
                expected_type = type_hints.get(field.name)
                if expected_type and not isinstance(value, expected_type):
                    raise ConfigError(
                        f"Field {field.name} has invalid type {type(value)}, "
                        f"expected {expected_type}"
                    )
    
    def validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ConfigError: If validation fails.
        """
        pass
    
    @classmethod
    def from_dict(cls: Type[T], config_dict: Dict[str, Any]) -> T:
        """Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values.
            
        Returns:
            T: Configuration instance.
            
        Raises:
            ConfigError: If dictionary is invalid.
        """
        try:
            return cls(**config_dict)
        except Exception as e:
            raise ConfigError(f"Failed to create config from dict: {e}")
    
    @classmethod
    def from_yaml(cls: Type[T], yaml_path: Path) -> T:
        """Load configuration from YAML file.
        
        Args:
            yaml_path: Path to YAML configuration file.
            
        Returns:
            T: Configuration instance.
            
        Raises:
            ConfigError: If YAML file is invalid or missing.
        """
        try:
            with open(yaml_path) as f:
                config_dict = yaml.safe_load(f)
            return cls.from_dict(config_dict)
        except Exception as e:
            raise ConfigError(f"Failed to load config from {yaml_path}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary.
        """
        return {
            k: v for k, v in self.__dict__.items() 
            if not k.startswith("_")
        }
    
    def save(self, yaml_path: Optional[Path] = None) -> None:
        """Save configuration to YAML file.
        
        Args:
            yaml_path: Path to save YAML file. Uses config_path if not provided.
            
        Raises:
            ConfigError: If save fails.
        """
        yaml_path = yaml_path or self.config_path
        if not yaml_path:
            raise ConfigError("No path provided for saving config")
            
        try:
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(yaml_path, "w") as f:
                yaml.safe_dump(self.to_dict(), f)
        except Exception as e:
            raise ConfigError(f"Failed to save config to {yaml_path}: {e}") 