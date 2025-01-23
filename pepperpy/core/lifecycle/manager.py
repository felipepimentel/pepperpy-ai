"""Lifecycle management implementation for Pepperpy framework."""

from typing import Dict, Any, Optional
from datetime import datetime

from .. import LifecycleManager
from ..utils.logger import get_logger
from .initializer import PepperpyInitializer
from .terminator import PepperpyTerminator

logger = get_logger(__name__)

class PepperpyLifecycleManager(LifecycleManager):
    """Lifecycle manager implementation for Pepperpy framework."""
    
    def __init__(self):
        """Initialize the lifecycle manager."""
        self._state = "uninitialized"
        self._initializer = PepperpyInitializer()
        self._terminator = PepperpyTerminator()
        self._metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat()
        }
    
    async def initialize(self) -> None:
        """Initialize the component."""
        if self._state != "uninitialized":
            logger.warning(f"Component already initialized (state: {self._state})")
            return
        
        try:
            await self._initializer.initialize()
            self._state = "initialized"
            self._metadata["initialized_at"] = datetime.now().isoformat()
            logger.info("Component initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize component: {str(e)}")
            self._state = "error"
            self._metadata["error"] = str(e)
            raise
    
    async def terminate(self) -> None:
        """Terminate the component."""
        if self._state not in ["initialized", "error"]:
            logger.warning(f"Component not initialized (state: {self._state})")
            return
        
        try:
            await self._terminator.terminate()
            self._state = "terminated"
            self._metadata["terminated_at"] = datetime.now().isoformat()
            logger.info("Component terminated successfully")
        except Exception as e:
            logger.error(f"Failed to terminate component: {str(e)}")
            self._state = "error"
            self._metadata["error"] = str(e)
            raise
    
    def get_state(self) -> str:
        """Get the current lifecycle state.
        
        Returns:
            Current state string.
        """
        return self._state
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get lifecycle metadata.
        
        Returns:
            Dictionary containing lifecycle metadata.
        """
        return self._metadata.copy()
    
    def get_init_steps(self) -> Dict[str, Any]:
        """Get initialization steps.
        
        Returns:
            Dictionary containing initialization steps and metadata.
        """
        return {
            "steps": self._initializer.get_init_steps(),
            "state": self._state,
            "metadata": self._metadata.copy()
        }
    
    def get_term_steps(self) -> Dict[str, Any]:
        """Get termination steps.
        
        Returns:
            Dictionary containing termination steps and metadata.
        """
        return {
            "steps": self._terminator.get_term_steps(),
            "state": self._state,
            "metadata": self._metadata.copy()
        } 