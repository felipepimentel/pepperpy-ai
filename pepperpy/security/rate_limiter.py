"""Rate limiter implementation."""

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..common.errors import PepperpyError
from .base import SecurityComponent, SecurityError


logger = logging.getLogger(__name__)


class RateLimiter(SecurityComponent):
    """Rate limiter implementation."""
    
    def __init__(
        self,
        name: str,
        max_requests: int = 100,
        time_window: int = 60,  # seconds
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize rate limiter.
        
        Args:
            name: Component name
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
            config: Optional component configuration
        """
        super().__init__(name, config)
        self._max_requests = max_requests
        self._time_window = time_window
        self._requests: Dict[str, List[float]] = defaultdict(list)
        
    @property
    def max_requests(self) -> int:
        """Return maximum requests per time window."""
        return self._max_requests
        
    @property
    def time_window(self) -> int:
        """Return time window in seconds."""
        return self._time_window
        
    async def _initialize(self) -> None:
        """Initialize rate limiter."""
        await super()._initialize()
        
    async def _cleanup(self) -> None:
        """Clean up rate limiter."""
        await super()._cleanup()
        self._requests.clear()
        
    def _clean_old_requests(self, key: str) -> None:
        """Clean old requests for key.
        
        Args:
            key: Request key
        """
        current_time = time.time()
        cutoff_time = current_time - self._time_window
        
        # Remove requests older than time window
        self._requests[key] = [
            timestamp for timestamp in self._requests[key]
            if timestamp > cutoff_time
        ]
        
    async def validate(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate request against rate limit.
        
        Args:
            input_data: Request key
            context: Optional validation context
            
        Returns:
            True if request is allowed, False otherwise
            
        Raises:
            SecurityError: If validation fails
        """
        try:
            # Convert input to key
            if isinstance(input_data, str):
                key = input_data
            else:
                raise SecurityError(f"Invalid input type: {type(input_data)}")
                
            # Clean old requests
            self._clean_old_requests(key)
            
            # Check request count
            return len(self._requests[key]) < self._max_requests
            
        except Exception as e:
            raise SecurityError(f"Rate limit validation failed: {e}") from e
            
    async def sanitize(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Record request and enforce rate limit.
        
        Args:
            input_data: Request key
            context: Optional sanitization context
            
        Returns:
            Request key if allowed
            
        Raises:
            SecurityError: If rate limit exceeded
        """
        try:
            # Convert input to key
            if isinstance(input_data, str):
                key = input_data
            else:
                raise SecurityError(f"Invalid input type: {type(input_data)}")
                
            # Clean old requests
            self._clean_old_requests(key)
            
            # Check rate limit
            if len(self._requests[key]) >= self._max_requests:
                raise SecurityError(
                    f"Rate limit exceeded for {key}: "
                    f"{self._max_requests} requests per {self._time_window} seconds"
                )
                
            # Record request
            self._requests[key].append(time.time())
            return key
            
        except Exception as e:
            raise SecurityError(f"Rate limit enforcement failed: {e}") from e
