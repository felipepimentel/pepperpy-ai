"""Base LLM model interface."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, TypeVar

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import ModelError, ModelRequestError, ModelResponseError
from ...core.lifecycle import Lifecycle
from ...core.context import Context
from ..types import Message


T = TypeVar("T")


class LLMModel(Lifecycle, ABC):
    """Base LLM model class."""
    
    def __init__(
        self,
        name: str,
        model_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize model.
        
        Args:
            name: Model name
            model_id: Model identifier
            config: Optional model configuration
        """
        super().__init__(name)
        self._model_id = model_id
        self._config = config or {}
        
    @property
    def model_id(self) -> str:
        """Return model identifier."""
        return self._model_id
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return model configuration."""
        return self._config
        
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        **kwargs: Any,
    ) -> Message:
        """Generate response for messages.
        
        Args:
            messages: Input messages
            **kwargs: Additional generation parameters
            
        Returns:
            Generated message
        """
        pass
        
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming response for messages.
        
        Args:
            messages: Input messages
            **kwargs: Additional generation parameters
            
        Returns:
            Async iterator of generated chunks
        """
        pass
        
    def validate(self) -> None:
        """Validate model state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Model name cannot be empty")
            
        if not self._model_id:
            raise ValueError("Model ID cannot be empty") 