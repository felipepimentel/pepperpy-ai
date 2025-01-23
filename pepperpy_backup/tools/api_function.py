"""API function implementation.

This module provides functionality for defining and executing API functions,
including parameter validation, error handling, and rate limiting.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.events import Event, EventBus
from pepperpy.monitoring import Monitor
from pepperpy.security import RateLimiter
from pepperpy.security.validator import Validator

T = TypeVar("T")


class FunctionError(PepperpyError):
    """Function error."""
    pass


@dataclass
class Parameter:
    """Function parameter."""
    
    name: str
    """Parameter name."""
    
    type: Type[Any]
    """Parameter type."""
    
    description: str
    """Parameter description."""
    
    required: bool = True
    """Whether parameter is required."""
    
    default: Optional[Any] = None
    """Default parameter value."""
    
    def validate(self, value: Any) -> None:
        """Validate parameter value.
        
        Args:
            value: Parameter value
            
        Raises:
            FunctionError: If validation fails
        """
        if value is None:
            if self.required:
                raise FunctionError(
                    f"Missing required parameter: {self.name}"
                )
            return
            
        if not isinstance(value, self.type):
            raise FunctionError(
                f"Invalid type for parameter {self.name}: "
                f"expected {self.type.__name__}, got {type(value).__name__}"
            )


@dataclass
class APIFunction(Lifecycle, ABC):
    """API function interface."""
    
    name: str
    """Function name."""
    
    description: str
    """Function description."""
    
    parameters: List[Parameter]
    """Function parameters."""
    
    event_bus: Optional[EventBus] = None
    """Optional event bus."""
    
    monitor: Optional[Monitor] = None
    """Optional monitor."""
    
    rate_limiter: Optional[RateLimiter] = None
    """Optional rate limiter."""
    
    validator: Optional[Validator] = None
    """Optional validator."""
    
    config: Optional[Dict[str, Any]] = None
    """Optional configuration."""
    
    def __post_init__(self) -> None:
        """Initialize function."""
        super().__init__()
        self._config = self.config or {}
        
    def validate_parameters(self, params: Dict[str, Any]) -> None:
        """Validate function parameters.
        
        Args:
            params: Parameter values
            
        Raises:
            FunctionError: If validation fails
        """
        # Check required parameters
        param_names = {p.name for p in self.parameters}
        for name in params:
            if name not in param_names:
                raise FunctionError(f"Unknown parameter: {name}")
                
        # Validate parameter values
        for param in self.parameters:
            value = params.get(param.name, param.default)
            param.validate(value)
            
        # Custom validation
        if self.validator:
            try:
                self.validator.validate(params)
            except Exception as e:
                raise FunctionError(f"Parameter validation failed: {e}")
                
    async def execute(self, params: Dict[str, Any]) -> T:
        """Execute function.
        
        Args:
            params: Parameter values
            
        Returns:
            Function result
            
        Raises:
            FunctionError: If execution fails
        """
        # Validate parameters
        self.validate_parameters(params)
        
        # Check rate limit
        if self.rate_limiter:
            try:
                await self.rate_limiter.check()
            except Exception as e:
                raise FunctionError(f"Rate limit exceeded: {e}")
                
        # Execute function
        try:
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        type="function_started",
                        source=self.name,
                        timestamp=datetime.now(),
                        data={"params": params},
                    )
                )
                
            result = await self._execute(params)
            
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        type="function_completed",
                        source=self.name,
                        timestamp=datetime.now(),
                        data={
                            "params": params,
                            "result": result,
                        },
                    )
                )
                
            return result
        except Exception as e:
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        type="function_failed",
                        source=self.name,
                        timestamp=datetime.now(),
                        data={
                            "params": params,
                            "error": str(e),
                        },
                    )
                )
                
            raise FunctionError(f"Function execution failed: {e}")
            
    @abstractmethod
    async def _execute(self, params: Dict[str, Any]) -> T:
        """Execute function implementation.
        
        Args:
            params: Parameter values
            
        Returns:
            Function result
            
        Raises:
            Exception: If execution fails
        """
        pass
        
    async def _initialize(self) -> None:
        """Initialize function."""
        if self.event_bus:
            await self.event_bus.initialize()
            
        if self.monitor:
            await self.monitor.initialize()
            
        if self.rate_limiter:
            await self.rate_limiter.initialize()
            
        if self.validator:
            await self.validator.initialize()
            
    async def _cleanup(self) -> None:
        """Clean up function."""
        if self.validator:
            await self.validator.cleanup()
            
        if self.rate_limiter:
            await self.rate_limiter.cleanup()
            
        if self.monitor:
            await self.monitor.cleanup()
            
        if self.event_bus:
            await self.event_bus.cleanup()
            
    def validate(self) -> None:
        """Validate function state."""
        super().validate()
        
        if not self.name:
            raise FunctionError("Empty function name")
            
        if not self.description:
            raise FunctionError("Empty function description")
            
        if not self.parameters:
            raise FunctionError("No function parameters")
            
        if self.event_bus:
            self.event_bus.validate()
            
        if self.monitor:
            self.monitor.validate()
            
        if self.rate_limiter:
            self.rate_limiter.validate()
            
        if self.validator:
            self.validator.validate() 