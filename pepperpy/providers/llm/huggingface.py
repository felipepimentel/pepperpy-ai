"""HuggingFace LLM provider implementation."""

import aiohttp
import asyncio
import json
import time
import logging
from typing import AsyncIterator, Dict, Any, AsyncGenerator, Optional

from pepperpy.providers.llm.base import BaseLLMProvider
from pepperpy.providers.llm.types import LLMConfig

logger = logging.getLogger(__name__)

@BaseLLMProvider.register("huggingface")
class HuggingFaceProvider(BaseLLMProvider):
    """HuggingFace LLM provider implementation."""
    
    def __init__(self, config: LLMConfig) -> None:
        """Initialize provider.
        
        Args:
            config: Provider configuration.
        """
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0.0
        self.min_request_interval = config.min_request_interval
        self._config = config.to_dict()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get provider configuration.
        
        Returns:
            Provider configuration.
        """
        return self._config
    
    @config.setter
    def config(self, value: Dict[str, Any]) -> None:
        """Set provider configuration.
        
        Args:
            value: Provider configuration.
        """
        self._config = value
    
    @property
    def name(self) -> str:
        """Get provider name.
        
        Returns:
            Provider name.
        """
        return "huggingface"
    
    async def _initialize_impl(self) -> None:
        """Initialize provider resources."""
        self._session = aiohttp.ClientSession(headers={"Authorization": f"Bearer {self.api_key}"})
    
    async def _cleanup_impl(self) -> None:
        """Clean up provider resources."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait for rate limit."""
        # TODO: Implement rate limiting
        pass
    
    async def _generate_impl(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Returns:
            Generated text.
            
        Raises:
            RuntimeError: If generation fails.
        """
        if not self._session:
            raise RuntimeError("Provider not initialized")
        
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{self.model}"
        payload = {
            "inputs": prompt,
            **kwargs
        }
        
        response = await self._session.post(url, json=payload)
        if response.status != 200:
            error_text = await response.text()
            raise RuntimeError(f"HuggingFace API error: {error_text}")
        
        result = await response.json()
        return result[0]["generated_text"]
    
    async def _stream_impl(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream text generation from prompt.
        
        Args:
            prompt: Input prompt.
            **kwargs: Additional generation parameters.
            
        Yields:
            Generated text chunks.
            
        Raises:
            RuntimeError: If generation fails.
        """
        if not self._session:
            raise RuntimeError("Provider not initialized")
        
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{self.model}"
        payload = {
            "inputs": prompt,
            "stream": True,
            **kwargs
        }
        
        response = await self._session.post(url, json=payload)
        if response.status != 200:
            error_text = await response.text()
            raise RuntimeError(f"HuggingFace API error: {error_text}")
        
        async for line in response.content:
            try:
                chunk = json.loads(line)
                yield chunk["token"]["text"]
            except json.JSONDecodeError:
                continue 
