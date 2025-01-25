"""Base provider implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime

from ..interfaces import Provider


class BaseProvider(ABC, Provider):
    """Base provider implementation."""
    
    def __init__(
        self,
        name: str,
        *,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider.
        
        Args:
            name: Provider name
            config: Optional configuration
        """
        if not name:
            raise ValueError("Provider name cannot be empty")
            
        self._name = name
        self._config = config or {}
        self._initialized = False
        self._initialized_at: Optional[datetime] = None
        self._cleaned_up = False
        self._cleaned_up_at: Optional[datetime] = None
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return self._name
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get provider configuration."""
        return self._config.copy()
        
    @property
    def is_initialized(self) -> bool:
        """Whether provider is initialized."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize provider."""
        if self._initialized:
            return
            
        try:
            await self._initialize_impl()
            self._initialized = True
            self._initialized_at = datetime.now()
        except Exception as e:
            self._initialized = False
            self._initialized_at = None
            raise e
            
    async def cleanup(self) -> None:
        """Clean up provider."""
        if not self._initialized or self._cleaned_up:
            return
            
        try:
            await self._cleanup_impl()
            self._cleaned_up = True
            self._cleaned_up_at = datetime.now()
        except Exception as e:
            self._cleaned_up = False
            self._cleaned_up_at = None
            raise e
            
    def validate(self) -> None:
        """Validate provider state."""
        if not self._name:
            raise ValueError("Empty provider name")
            
        self._validate_impl()
        
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Initialize provider implementation."""
        pass
        
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Clean up provider implementation."""
        pass
        
    def _validate_impl(self) -> None:
        """Validate provider implementation."""
        pass 