"""OpenRouter LLM provider implementation."""

import aiohttp
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

@BaseLLMProvider.register("openrouter")
class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter LLM provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the OpenRouter provider.
        
        Args:
            config: Configuration dictionary containing:
                - api_key: OpenRouter API key
                - model: Model to use (e.g. "anthropic/claude-2")
                - base_url: Optional base URL override
        """
        super().__init__(config)
        self.api_key = config["api_key"]
        self.model = config["model"]
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.session: Optional[aiohttp.ClientSession] = None
    
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
                    "HTTP-Referer": "https://github.com/pimentel/pepperpy",
                    "X-Title": "Pepperpy"
                }
            )
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter provider: {str(e)}")
            await self.cleanup()
            raise ValueError(f"OpenRouter initialization failed: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False
    
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
            
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        
        try:
            async with self.session.post(f"{self.base_url}/chat/completions", json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenRouter API error: {error_text}")
                    
                result = await response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"OpenRouter generation failed: {str(e)}")
            raise RuntimeError(f"OpenRouter generation failed: {str(e)}")
    
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
            
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **kwargs
        }
        
        try:
            async with self.session.post(f"{self.base_url}/chat/completions", json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenRouter API error: {error_text}")
                    
                async for line in response.content:
                    if line:
                        try:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                line = line[6:]  # Remove "data: " prefix
                                if line == "[DONE]":
                                    break
                                    
                                chunk = json.loads(line)
                                if chunk["choices"][0]["finish_reason"] is not None:
                                    break
                                    
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                                    
                        except Exception as e:
                            logger.error(f"Error parsing stream chunk: {str(e)}")
                            continue
                            
        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {str(e)}")
            raise RuntimeError(f"OpenRouter streaming failed: {str(e)}") 