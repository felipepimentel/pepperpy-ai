"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Any

from pepperpy_ai.responses import AIResponse


class BaseProvider(ABC):
    """Base provider interface.
    
    This class defines the interface that all AI providers must implement.
    """
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Complete a prompt.
        
        Args:
            prompt: The prompt to complete
            **kwargs: Additional provider-specific arguments
            
        Returns:
            The AI response
        """
        raise NotImplementedError
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Stream responses for a prompt.
        
        Args:
            prompt: The prompt to stream
            **kwargs: Additional provider-specific arguments
            
        Returns:
            The AI response
        """
        raise NotImplementedError
