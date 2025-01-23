"""Input validator implementation."""

import logging
import re
from typing import Any, Dict, List, Optional, Pattern

from ..common.errors import PepperpyError
from .base import SecurityComponent, SecurityError


logger = logging.getLogger(__name__)


class InputValidator(SecurityComponent):
    """Input validator implementation."""
    
    def __init__(
        self,
        name: str,
        patterns: Optional[Dict[str, Pattern[str]]] = None,
        max_length: Optional[int] = None,
        allowed_types: Optional[List[type]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize input validator.
        
        Args:
            name: Component name
            patterns: Optional regex patterns for validation
            max_length: Optional maximum input length
            allowed_types: Optional list of allowed types
            config: Optional component configuration
        """
        super().__init__(name, config)
        self._patterns = patterns or {}
        self._max_length = max_length
        self._allowed_types = allowed_types or []
        
    @property
    def patterns(self) -> Dict[str, Pattern[str]]:
        """Return validation patterns."""
        return self._patterns
        
    @property
    def max_length(self) -> Optional[int]:
        """Return maximum input length."""
        return self._max_length
        
    @property
    def allowed_types(self) -> List[type]:
        """Return allowed types."""
        return self._allowed_types
        
    async def _initialize(self) -> None:
        """Initialize input validator."""
        await super()._initialize()
        
    async def _cleanup(self) -> None:
        """Clean up input validator."""
        await super()._cleanup()
        
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
        try:
            # Check type
            if self._allowed_types and not any(
                isinstance(input_data, t) for t in self._allowed_types
            ):
                return False
                
            # Check length
            if self._max_length is not None:
                if isinstance(input_data, (str, bytes, list, tuple, dict)):
                    if len(input_data) > self._max_length:
                        return False
                        
            # Check patterns
            if isinstance(input_data, str):
                for pattern in self._patterns.values():
                    if pattern.search(input_data):
                        return False
                        
            return True
            
        except Exception as e:
            raise SecurityError(f"Input validation failed: {e}") from e
            
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
        try:
            # Handle strings
            if isinstance(input_data, str):
                sanitized = input_data
                
                # Apply patterns
                for pattern in self._patterns.values():
                    sanitized = pattern.sub("", sanitized)
                    
                # Truncate if needed
                if self._max_length is not None:
                    sanitized = sanitized[:self._max_length]
                    
                return sanitized
                
            # Handle lists and tuples
            elif isinstance(input_data, (list, tuple)):
                if self._max_length is not None:
                    return input_data[:self._max_length]
                return input_data
                
            # Handle dictionaries
            elif isinstance(input_data, dict):
                if self._max_length is not None:
                    return dict(list(input_data.items())[:self._max_length])
                return input_data
                
            # Return as is for other types
            return input_data
            
        except Exception as e:
            raise SecurityError(f"Input sanitization failed: {e}") from e
