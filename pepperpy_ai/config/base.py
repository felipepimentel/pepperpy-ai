"""Base configuration types."""

from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional
from datetime import datetime

from ..types import JsonDict, Serializable

@dataclass
class BaseConfigData:
    """Base configuration data without defaults.
    
    This class defines the minimum required configuration fields
    that all configurations must have.
    
    Attributes:
        name: Configuration name
        version: Configuration version
        enabled: Whether the configuration is enabled
    """
    name: str
    version: str
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate configuration data."""
        if not self.name:
            raise ValueError("Configuration name cannot be empty")
        if not self.version:
            raise ValueError("Configuration version cannot be empty")

@dataclass
class BaseConfig(BaseConfigData, Serializable):
    """Base configuration with defaults.
    
    This class extends BaseConfigData with additional fields and
    functionality common to all configurations.
    
    Attributes:
        metadata: Additional configuration metadata
        settings: Configuration settings
        created_at: Configuration creation timestamp
        updated_at: Configuration update timestamp
    """
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Configuration schema version
    SCHEMA_VERSION: ClassVar[str] = "1.0.0"

    def __post_init__(self) -> None:
        """Initialize and validate configuration."""
        super().__post_init__()
        self.metadata.setdefault("schema_version", self.SCHEMA_VERSION)

    def to_dict(self) -> JsonDict:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "BaseConfig":
        """Create configuration from dictionary.
        
        Args:
            data: Configuration data
            
        Returns:
            Configuration instance
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            return cls(
                name=data["name"],
                version=data["version"],
                enabled=data.get("enabled", True),
                metadata=data.get("metadata", {}),
                settings=data.get("settings", {}),
                created_at=datetime.fromisoformat(
                    data.get("created_at", datetime.now().isoformat())
                ),
                updated_at=datetime.fromisoformat(
                    data.get("updated_at", datetime.now().isoformat())
                ),
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    def update(self, **kwargs: Any) -> None:
        """Update configuration settings.
        
        Args:
            **kwargs: Settings to update
        """
        self.settings.update(kwargs)
        self.updated_at = datetime.now()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting.
        
        Args:
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            Setting value
        """
        return self.settings.get(key, default)

    def validate(self) -> None:
        """Validate configuration.
        
        This method should be overridden by subclasses to implement
        configuration-specific validation.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
