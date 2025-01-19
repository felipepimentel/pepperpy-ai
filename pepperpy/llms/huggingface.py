"""HuggingFace LLM module using OpenRouter API."""

import os
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict

import aiohttp
import json
import asyncio

from pepperpy.llms.base_llm import BaseLLM, LLMConfig, LLMResponse


class HuggingFaceLLM(BaseLLM):
    """HuggingFace LLM client using OpenRouter API."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize HuggingFace LLM client.
        
        Args:
            config: LLM configuration
        """
        super().__init__(config)
        self.session: aiohttp.ClientSession | None = None
        self.last_request_time = 0.0
        self.min_request_interval = 2.0  # Minimum seconds between requests

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession(
            base_url="https://openrouter.ai/",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "HTTP-Referer": "https://github.com/felipepimentel/pepperpy-ai",
                "X-Title": "PepperPy",
                "Content-Type": "application/json",
            },
        )

    async def generate(
        self,
        prompt: str,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text completion.
        
        Args:
            prompt: Input prompt
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters
            
        Returns:
            Generated response
            
        Raises:
            Exception: If generation fails
        """
        if not self.session:
            raise RuntimeError("Client not initialized")

        # Rate limiting
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

        data = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        if stop:
            data["stop"] = stop

        print(f"\nSending request to OpenRouter API...")
        print(f"Model: {self.config.model_name}")
        print(f"Prompt: {prompt[:100]}...")

        async with self.session.post("api/v1/chat/completions", json=data) as response:
            if response.status != 200:
                text = await response.text()
                if response.status == 429:  # Rate limit
                    print("Rate limit hit, waiting before retry...")
                    await asyncio.sleep(5)  # Wait 5 seconds
                    return await self.generate(prompt, stop, temperature, max_tokens, **kwargs)  # Retry
                raise Exception(f"API request failed ({response.status}): {text}")

            result = await response.json()
            if "error" in result:
                if "code" in result["error"] and result["error"]["code"] == 429:
                    print("Rate limit hit, waiting before retry...")
                    await asyncio.sleep(5)  # Wait 5 seconds
                    return await self.generate(prompt, stop, temperature, max_tokens, **kwargs)  # Retry
                raise Exception(f"API error: {json.dumps(result['error'], indent=2)}")

            print(f"Raw response: {json.dumps(result, indent=2)}")

            return LLMResponse(
                text=result["choices"][0]["message"]["content"],
                tokens_used=result["usage"]["total_tokens"],
                finish_reason=result["choices"][0]["finish_reason"],
                model_name=result["model"],
            )

    async def generate_stream(
        self,
        prompt: str,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate streaming text completion.
        
        Args:
            prompt: Input prompt
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters
            
        Returns:
            Generated response chunks
            
        Raises:
            Exception: If generation fails
        """
        # For now, we don't support streaming
        response = await self.generate(prompt, stop, temperature, max_tokens, **kwargs)
        yield response.text

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            Exception: If embedding generation fails
        """
        raise NotImplementedError("Embedding generation not supported yet")
