"""Token handler implementation.

This module provides functionality for managing API tokens,
including token validation, rotation, and rate limiting.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.events import Event, EventBus
from pepperpy.monitoring import Monitor
from pepperpy.security import RateLimiter


class TokenError(PepperpyError):
    """Token error."""
    pass


class TokenHandler(Lifecycle):
    """Token handler implementation."""
    
    def __init__(
        self,
        name: str,
        token: str,
        rate_limiter: Optional[RateLimiter] = None,
        event_bus: Optional[EventBus] = None,
        monitor: Optional[Monitor] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize handler.
        
        Args:
            name: Handler name
            token: API token
            rate_limiter: Optional rate limiter
            event_bus: Optional event bus
            monitor: Optional monitor
            config: Optional configuration
        """
        super().__init__()
        self.name = name
        self._token = token
        self._rate_limiter = rate_limiter
        self._event_bus = event_bus
        self._monitor = monitor
        self._config = config or {}
        self._created_at = datetime.now()
        self._last_used_at: Optional[datetime] = None
        self._use_count = 0
        self._is_valid = True
        
    @property
    def token(self) -> str:
        """Get API token.
        
        Returns:
            API token
            
        Raises:
            TokenError: If token is invalid
        """
        if not self._is_valid:
            raise TokenError("Token is invalid")
            
        return self._token
        
    @property
    def use_count(self) -> int:
        """Get token use count.
        
        Returns:
            Token use count
        """
        return self._use_count
        
    async def use_token(self) -> str:
        """Use API token.
        
        Returns:
            API token
            
        Raises:
            TokenError: If token is invalid or rate limit exceeded
        """
        if not self._is_valid:
            raise TokenError("Token is invalid")
            
        if self._rate_limiter:
            try:
                await self._rate_limiter.check()
            except Exception as e:
                raise TokenError(f"Rate limit exceeded: {e}")
                
        self._last_used_at = datetime.now()
        self._use_count += 1
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="token_used",
                    source=self.name,
                    timestamp=self._last_used_at,
                    data={
                        "use_count": self._use_count,
                    },
                )
            )
            
        return self._token
        
    async def invalidate(self) -> None:
        """Invalidate token."""
        self._is_valid = False
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="token_invalidated",
                    source=self.name,
                    timestamp=datetime.now(),
                    data={
                        "use_count": self._use_count,
                    },
                )
            )
            
    async def rotate(self, new_token: str) -> None:
        """Rotate token.
        
        Args:
            new_token: New API token
            
        Raises:
            TokenError: If token is invalid
        """
        if not new_token:
            raise TokenError("Empty token")
            
        old_token = self._token
        self._token = new_token
        self._created_at = datetime.now()
        self._last_used_at = None
        self._use_count = 0
        self._is_valid = True
        
        if self._event_bus:
            await self._event_bus.publish(
                Event(
                    type="token_rotated",
                    source=self.name,
                    timestamp=self._created_at,
                    data={
                        "old_token_use_count": self._use_count,
                    },
                )
            )
            
    async def _initialize(self) -> None:
        """Initialize handler."""
        if self._rate_limiter:
            await self._rate_limiter.initialize()
            
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
    async def _cleanup(self) -> None:
        """Clean up handler."""
        if self._monitor:
            await self._monitor.cleanup()
            
        if self._event_bus:
            await self._event_bus.cleanup()
            
        if self._rate_limiter:
            await self._rate_limiter.cleanup()
            
    def validate(self) -> None:
        """Validate handler state."""
        super().validate()
        
        if not self.name:
            raise TokenError("Empty handler name")
            
        if not self._token:
            raise TokenError("Empty token")
            
        if self._rate_limiter:
            self._rate_limiter.validate()
            
        if self._event_bus:
            self._event_bus.validate()
            
        if self._monitor:
            self._monitor.validate() 