"""Anthropic LLM provider implementation."""
from typing import Any, Dict, List, Optional

from anthropic import AsyncAnthropic
from anthropic.types import Message

from ..base.provider import BaseProvider, ProviderConfig

class AnthropicProvider(BaseProvider):
    """Provider for Anthropic language models."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the Anthropic provider."""
        super().__init__(config)
        self.client = None
        self.model = config.parameters.get("model", "claude-3-opus-20240229")
    
    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self._initialized:
            api_key = self.config.parameters.get("api_key")
            if not api_key:
                raise ValueError("Anthropic API key is required")
            
            self.client = AsyncAnthropic(api_key=api_key)
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.close()
            self._initialized = False
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None
    ) -> Message:
        """Generate completion for the given messages."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop_sequences=stop
        )
        
        return response 