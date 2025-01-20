"""Runtime environment management for Pepperpy.

This module provides functionality for managing the runtime environment,
including configuration, dependencies, and resource management.
"""

import logging
import os
from typing import Any, Dict, Optional

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class EnvironmentError(PepperpyError):
    """Environment error."""
    pass


class Environment(Lifecycle):
    """Runtime environment manager."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize environment.
        
        Args:
            name: Environment name
            config: Optional environment configuration
        """
        super().__init__()
        self.name = name
        self._config = config or {}
        self._resources: Dict[str, Any] = {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get environment configuration."""
        return self._config
        
    async def initialize(self) -> None:
        """Initialize environment."""
        try:
            # Set up environment variables
            for key, value in self._config.get("env", {}).items():
                os.environ[key] = str(value)
                
            # Initialize resources
            for name, config in self._config.get("resources", {}).items():
                self._resources[name] = await self._init_resource(name, config)
                
        except Exception as e:
            logger.error(f"Failed to initialize environment: {e}")
            raise EnvironmentError(str(e))
            
    async def cleanup(self) -> None:
        """Clean up environment."""
        try:
            # Clean up resources
            for name, resource in self._resources.items():
                await self._cleanup_resource(name, resource)
                
            self._resources.clear()
            
        except Exception as e:
            logger.error(f"Failed to clean up environment: {e}")
            raise EnvironmentError(str(e))
            
    async def _init_resource(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> Any:
        """Initialize resource.
        
        Args:
            name: Resource name
            config: Resource configuration
            
        Returns:
            Initialized resource
            
        Raises:
            EnvironmentError: If resource initialization fails
        """
        raise NotImplementedError
        
    async def _cleanup_resource(
        self,
        name: str,
        resource: Any,
    ) -> None:
        """Clean up resource.
        
        Args:
            name: Resource name
            resource: Resource to clean up
            
        Raises:
            EnvironmentError: If resource cleanup fails
        """
        raise NotImplementedError
        
    def validate(self) -> None:
        """Validate environment state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Environment name cannot be empty") 