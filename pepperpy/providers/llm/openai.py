"""OpenAI LLM provider implementation."""
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from ..base.provider import BaseProvider, ProviderConfig

class OpenAIProvider(BaseProvider):
    """Provider for OpenAI language models."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the OpenAI provider."""
        super().__init__(config)
        self.client = None
        self.model = config.parameters.get("model", "gpt-4-turbo-preview")
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self._initialized:
            api_key = self.config.parameters.get("api_key")
            if not api_key:
                raise ValueError("OpenAI API key is required")
            
            self.client = AsyncOpenAI(api_key=api_key)
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
    ) -> ChatCompletion:
        """Generate completion for the given messages."""
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop
        )
        
        return response 