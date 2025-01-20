"""Base security implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class SecurityError(PepperpyError):
    """Security error."""
    pass


class SecurityComponent(Lifecycle, ABC):
    """Security component implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize security component.
        
        Args:
            name: Component name
            config: Optional component configuration
        """
        super().__init__(name)
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return component configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize security component."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up security component."""
        pass
        
    @abstractmethod
    async def validate(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate input data.
        
        Args:
            input_data: Input data
            context: Optional validation context
            
        Returns:
            True if input is valid, False otherwise
            
        Raises:
            SecurityError: If validation fails
        """
        pass
        
    @abstractmethod
    async def sanitize(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Sanitize input data.
        
        Args:
            input_data: Input data
            context: Optional sanitization context
            
        Returns:
            Sanitized data
            
        Raises:
            SecurityError: If sanitization fails
        """
        pass 