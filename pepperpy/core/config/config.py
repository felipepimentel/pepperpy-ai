"""Configuration module for Pepperpy."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .errors import PepperpyError


logger = logging.getLogger(__name__)


class ConfigError(PepperpyError):
    """Configuration error."""
    pass


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        path: Optional path to config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigError: If loading fails
    """
    try:
        # Use default config path if not provided
        if not path:
            path = os.getenv("PEPPERPY_CONFIG", "config.yaml")
            
        # Load and parse YAML
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigError(f"Config file not found: {path}")
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        if not isinstance(config, dict):
            raise ConfigError("Invalid config format: must be a dictionary")
            
        return config
        
    except Exception as e:
        raise ConfigError(f"Failed to load config: {e}") from e


def save_config(config: Dict[str, Any], path: str) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary
        path: Path to save config file
        
    Raises:
        ConfigError: If saving fails
    """
    try:
        # Create parent directories if needed
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as YAML
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False)
            
    except Exception as e:
        raise ConfigError(f"Failed to save config: {e}") from e


def get_data_store_config(config: Dict[str, Any], store_type: str) -> Dict[str, Any]:
    """Get data store configuration.
    
    Args:
        config: Configuration dictionary
        store_type: Data store type
        
    Returns:
        Data store configuration
        
    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Get data stores section
        stores_config = config.get("data_stores", {})
        if not isinstance(stores_config, dict):
            raise ConfigError("Invalid data_stores config: must be a dictionary")
            
        # Get store config
        store_config = stores_config.get(store_type)
        if store_config is None:
            raise ConfigError(f"Data store type not found: {store_type}")
            
        if not isinstance(store_config, dict):
            raise ConfigError(f"Invalid config for store type {store_type}: must be a dictionary")
            
        return store_config
        
    except Exception as e:
        raise ConfigError(f"Failed to get data store config: {e}") from e 