"""API function implementation.

This module provides functionality for managing API functions,
including parameter validation, rate limiting, and error handling.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic, Type
from dataclasses import dataclass
import logging

from ..core.errors import PepperpyError
from ..core.events import Event, EventBus
from ..core.security import RateLimiter
from ..interfaces import BaseProvider
from ..monitoring import Monitor

logger = logging.getLogger(__name__)

T = TypeVar("T")

class APIFunctionError(PepperpyError):
    """API function error."""
    pass

@dataclass
class Parameter:
    """Function parameter."""
    
    name: str
    type: Type[Any]
    description: str
    required: bool = True
    default: Any = None
    
    def validate(self, value: Any) -> None:
        """Validate parameter value.
        
        Args:
            value: Parameter value to validate
            
        Raises:
            APIFunctionError: If validation fails
        """
        if value is None:
            if self.required:
                raise APIFunctionError(
                    f"Missing required parameter: {self.name}"
                )
            return
            
        if not isinstance(value, self.type):
            raise APIFunctionError(
                f"Invalid type for parameter {self.name}: "
                f"expected {self.type.__name__}, got {type(value).__name__}"
            )

class BaseAPIFunction(BaseProvider, Generic[T]):
    """Base API function implementation."""
    
    def __init__(
        self,
        name: str,
        function: str,
        parameters: Dict[str, Parameter],
        rate_limiter: Optional[RateLimiter] = None,
        event_bus: Optional[EventBus] = None,
        monitor: Optional[Monitor] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize function.
        
        Args:
            name: Function name
            function: API function name
            parameters: Function parameters
            rate_limiter: Optional rate limiter
            event_bus: Optional event bus
            monitor: Optional monitor
            config: Optional configuration
        """
        super().__init__(
            name=name,
            config=config,
        )
        self._function = function
        self._parameters = parameters
        self._rate_limiter = rate_limiter
        self._event_bus = event_bus
        self._monitor = monitor
        self._created_at = datetime.now()
        self._last_used_at: Optional[datetime] = None
        self._use_count = 0
        self._is_valid = True
        
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
        if self._rate_limiter:
            await self._rate_limiter.initialize()
            
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        if self._rate_limiter:
            await self._rate_limiter.cleanup()
            
        if self._monitor:
            await self._monitor.cleanup()
            
        if self._event_bus:
            await self._event_bus.cleanup()
            
    async def _validate_impl(self) -> None:
        """Validate implementation."""
        if not self._function:
            raise APIFunctionError("Empty function name")
            
        if not self._parameters:
            raise APIFunctionError("Empty parameters")
            
        if self._event_bus:
            await self._event_bus.validate()
            
        if self._monitor:
            await self._monitor.validate()
            
        if self._rate_limiter:
            await self._rate_limiter.validate({
                "function": self._function,
                "parameters": self._parameters
            })
            
    @property
    def function(self) -> str:
        """Get API function name.
        
        Returns:
            API function name
            
        Raises:
            APIFunctionError: If function is invalid
        """
        if not self._is_valid:
            raise APIFunctionError("Function is invalid")
            
        return self._function
        
    @property
    def parameters(self) -> Dict[str, Parameter]:
        """Get function parameters.
        
        Returns:
            Function parameters
            
        Raises:
            APIFunctionError: If function is invalid
        """
        if not self._is_valid:
            raise APIFunctionError("Function is invalid")
            
        return self._parameters
        
    @property
    def use_count(self) -> int:
        """Get function use count.
        
        Returns:
            Function use count
        """
        return self._use_count
        
    @abstractmethod
    async def _execute_impl(self, params: Dict[str, Any]) -> T:
        """Execute function implementation.
        
        Args:
            params: Function parameters
            
        Returns:
            Function result
            
        Raises:
            APIFunctionError: If execution fails
        """
        pass
        
    async def execute(self, params: Dict[str, Any]) -> T:
        """Execute function.
        
        Args:
            params: Function parameters
            
        Returns:
            Function result
            
        Raises:
            APIFunctionError: If execution fails
        """
        # Validate parameters
        param_names = set(self._parameters.keys())
        for name in params:
            if name not in param_names:
                raise APIFunctionError(f"Unknown parameter: {name}")
                
        # Validate parameter values
        for name, param in self._parameters.items():
            value = params.get(name)
            param.validate(value)
            
        # Check rate limit
        if self._rate_limiter:
            try:
                await self._rate_limiter.check()
            except Exception as e:
                raise APIFunctionError(f"Rate limit exceeded: {e}")
                
        # Execute function
        try:
            result = await self._execute_impl(params)
            self._use_count += 1
            self._last_used_at = datetime.now()
            return result
        except Exception as e:
            raise APIFunctionError(f"Function execution failed: {e}")

    async def validate(self) -> None:
        """Validate function state."""
        await super().validate()
        
        if not self._function:
            raise APIFunctionError("Empty function name")
            
        if not self._parameters:
            raise APIFunctionError("Empty parameters")
            
        await self._validate_impl()
        
        if self._event_bus:
            await self._event_bus.validate()
            
        if self._monitor:
            await self._monitor.validate()
            
        if self._rate_limiter:
            await self._rate_limiter.validate({
                "function": self._function,
                "parameters": self._parameters
            }) 