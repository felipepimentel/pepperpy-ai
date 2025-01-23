"""Configuration management implementation for Pepperpy framework."""

from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

from .. import ConfigurationProvider
from ..utils.errors import ConfigurationError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ConfigManager(ConfigurationProvider):
    """Configuration manager implementation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Optional path to the configuration file.
                        If not provided, uses default location.
        """
        self.config_path = config_path or os.getenv(
            'PEPPERPY_CONFIG',
            str(Path.home() / '.pepperpy' / 'config.json')
        )
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)
            else:
                logger.warning(f"Config file not found at {self.config_path}")
                self._config = {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {str(e)}")
    
    def load(self) -> Dict[str, Any]:
        """Load configuration data.
        
        Returns:
            Dict containing configuration data.
        """
        return self._config.copy()
    
    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration data.
        
        Args:
            config: Configuration data to save.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            self._config = config.copy()
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key to get.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key to set.
            value: Value to set.
        """
        self._config[key] = value
        self.save(self._config)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values.
        
        Args:
            updates: Dictionary of updates to apply.
        """
        self._config.update(updates)
        self.save(self._config)
