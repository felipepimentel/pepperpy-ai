"""OpenRouter LLM provider."""

import json
import aiohttp
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from pepperpy.llms.base_llm import BaseLLM
from pepperpy.llms.types import LLMResponse, ProviderConfig


class OpenRouterProvider(BaseLLM):
    """OpenRouter LLM provider."""
    
    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider.
        
        Args:
            config: Provider configuration.
        """
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "HTTP-Referer": "https://github.com/pimentel/pepperpy",
            "X-Title": "PepperPy"
        }
    
    async def initialize(self) -> None:
        """Initialize provider resources."""
        if self.is_initialized:
            return
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            raise_for_status=True
        )
        self.is_initialized = True
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_initialized = False
    
    async def generate(self, prompt: str) -> LLMResponse:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            Generated text response.
            
        Raises:
            Exception: If generation fails.
        """
        if not self.is_initialized or not self.session:
            raise Exception("Provider not initialized")
        
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            **self.config.model_kwargs
        }
        
        if self.config.stop_sequences:
            payload["stop"] = self.config.stop_sequences
        
        async with self.session.post(
            f"{self.base_url}/chat/completions",
            json=payload
        ) as response:
            data = await response.json()
            print(f"\nAPI Response: {json.dumps(data, indent=2)}\n")  # Debug logging
            
            if "error" in data:
                error = data["error"]
                if error.get("code") == 429:  # Rate limit error
                    raise Exception(f"Rate limit exceeded: {error.get('message')}")
                raise Exception(f"API error: {error.get('message')}")
            
            # Update stats with safe defaults
            self.stats.total_requests += 1
            usage = data.get("usage", {})
            self.stats.total_tokens += usage.get("total_tokens", 0)
            self.stats.total_cost += usage.get("total_cost", 0)
            self.stats.last_success = datetime.now()
            
            # Extract response text safely
            choices = data.get("choices", [])
            response_text = choices[0]["message"]["content"] if choices else ""
            
            return LLMResponse(
                text=response_text,
                tokens_used=usage.get("total_tokens", 0),
                cost=usage.get("total_cost", 0),
                model_name=self.config.model_name,
                metadata={
                    "provider": "openrouter",
                    "response": data
                }
            )
    
    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate text from prompt in streaming mode.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            Iterator of generated text chunks.
            
        Raises:
            Exception: If generation fails.
        """
        if not self.is_initialized or not self.session:
            raise Exception("Provider not initialized")
        
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
            **self.config.model_kwargs
        }
        
        if self.config.stop_sequences:
            payload["stop"] = self.config.stop_sequences
        
        async with self.session.post(
            f"{self.base_url}/chat/completions",
            json=payload
        ) as response:
            # Update stats
            self.stats.total_requests += 1
            self.stats.last_success = datetime.now()
            
            async for line in response.content:
                if line.strip():
                    try:
                        data_str = line.decode("utf-8").strip()
                        if data_str.startswith("data: "):
                            data_str = data_str[6:]  # Remove "data: " prefix
                            if data_str == "[DONE]":
                                break
                            
                            data = json.loads(data_str)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                    except Exception:
                        continue
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text.
        
        Args:
            text: Input text.
            
        Returns:
            Embedding vector as list of floats.
            
        Raises:
            Exception: If embedding generation fails.
        """
        if not self.is_initialized or not self.session:
            raise Exception("Provider not initialized")
        
        payload = {
            "model": "text-embedding-ada-002",  # OpenRouter uses OpenAI's embedding model
            "input": text
        }
        
        async with self.session.post(
            f"{self.base_url}/embeddings",
            json=payload
        ) as response:
            data = await response.json()
            
            # Update stats
            self.stats.total_requests += 1
            self.stats.total_tokens += data["usage"]["total_tokens"]
            self.stats.total_cost += data["usage"]["total_cost"]
            self.stats.last_success = datetime.now()
            
            return data["data"][0]["embedding"]
