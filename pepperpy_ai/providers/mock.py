"""Mock provider for testing."""

from typing import Any

from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse


class MockProvider(BaseProvider):
    """Mock provider for testing.
    
    This provider returns predefined responses for testing purposes.
    """
    
    async def complete(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Mock completion method.
        
        Args:
            prompt: The prompt to complete
            **kwargs: Additional arguments (ignored)
            
        Returns:
            A mock response
        """
        return AIResponse(content="Mock completion")
    
    async def stream(self, prompt: str, **kwargs: Any) -> AIResponse:
        """Mock streaming method.
        
        Args:
            prompt: The prompt to stream
            **kwargs: Additional arguments (ignored)
            
        Returns:
            A mock response
        """
        return AIResponse(content="Mock stream") 