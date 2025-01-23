"""HuggingFace LLM provider implementation."""

import aiohttp
import asyncio
import json
import time
import logging
from typing import AsyncIterator, Dict, Any, AsyncGenerator, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

@BaseLLMProvider.register("huggingface")
class HuggingFaceProvider(BaseLLMProvider):
    """HuggingFace LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the HuggingFace provider.
        
        Args:
            config: Configuration dictionary containing:
                - api_key: HuggingFace API key
                - model: Model to use (e.g. "meta-llama/Llama-2-70b-chat-hf")
                - base_url: Optional base URL override
        """
        super().__init__(config)
        self.api_key = config["api_key"]
        self.model = config["model"]
        self.base_url = config.get("base_url", "https://api-inference.huggingface.co/models")
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0.0
        self.min_request_interval = config.get("min_request_interval", 2.0)
    
    async def initialize(self) -> bool:
        """Initialize the provider.
        
        Returns:
            True if initialization was successful.
            
        Raises:
            ValueError: If initialization fails.
        """
        if self.is_initialized:
            return True
            
        try:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace provider: {str(e)}")
            await self.cleanup()
            raise ValueError(f"HuggingFace initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False
    
    async def _wait_for_rate_limit(self):
        """Wait for rate limit if needed."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: The input prompt.
            **kwargs: Additional provider-specific arguments.
            
        Returns:
            The generated text.
            
        Raises:
            ValueError: If provider is not initialized.
            RuntimeError: If the API request fails.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.session:
            raise ValueError("Session not initialized")
            
        await self._wait_for_rate_limit()
            
        data = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": False,
                **kwargs
            }
        }
        
        try:
            async with self.session.post(f"{self.base_url}/{self.model}", json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"HuggingFace API error: {error_text}")
                    
                result = await response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                return ""
                
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {str(e)}")
            raise RuntimeError(f"HuggingFace generation failed: {str(e)}")
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream text generation from a prompt.
        
        Args:
            prompt: The input prompt.
            **kwargs: Additional provider-specific arguments.
            
        Yields:
            Generated text chunks.
            
        Raises:
            ValueError: If provider is not initialized.
            RuntimeError: If the API request fails.
        """
        if not self.is_initialized:
            raise ValueError("Provider not initialized")
            
        if not self.session:
            raise ValueError("Session not initialized")
            
        await self._wait_for_rate_limit()
            
        data = {
            "inputs": prompt,
            "parameters": {
                "return_full_text": False,
                "stream": True,
                **kwargs
            }
        }
        
        try:
            async with self.session.post(f"{self.base_url}/{self.model}", json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"HuggingFace API error: {error_text}")
                    
                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line)
                            if isinstance(chunk, list) and len(chunk) > 0:
                                if text := chunk[0].get("token", {}).get("text", ""):
                                    yield text
                                    
                        except Exception as e:
                            logger.error(f"Error parsing stream chunk: {str(e)}")
                            continue
                            
        except Exception as e:
            logger.error(f"HuggingFace streaming failed: {str(e)}")
            raise RuntimeError(f"HuggingFace streaming failed: {str(e)}") 
