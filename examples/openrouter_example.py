"""Example using OpenRouter API directly."""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator

import aiohttp
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class LLMConfig:
    """LLM configuration."""

    api_key: str
    model: str
    provider: str = "openrouter"
    temperature: float = 0.7
    max_tokens: int = 100


@dataclass
class LLMResponse:
    """LLM response."""

    text: str
    tokens_used: int
    model: str


class OpenRouterLLM:
    """OpenRouter LLM client."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize OpenRouter client.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession(
            base_url="https://openrouter.ai/api/v1/",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "HTTP-Referer": "https://github.com/felipepimentel/pepperpy-ai",
                "X-Title": "PepperPy Example",
                "Content-Type": "application/json",
            },
        )

    async def generate(self, prompt: str) -> LLMResponse:
        """Generate text completion.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response
            
        Raises:
            Exception: If generation fails
        """
        if not self.session:
            raise RuntimeError("Client not initialized")

        data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        print(f"\nSending request to OpenRouter API...")
        print(f"Model: {self.config.model}")
        print(f"API Key: {self.config.api_key[:10]}...")

        async with self.session.post("chat/completions", json=data) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"API request failed ({response.status}): {text}")

            result = await response.json()
            return LLMResponse(
                text=result["choices"][0]["message"]["content"],
                tokens_used=result["usage"]["total_tokens"],
                model=result["model"],
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None


async def main() -> None:
    """Run the example."""
    # Initialize LLM with configuration from environment
    api_key = os.getenv("PEPPERPY_API_KEY")
    if not api_key:
        raise ValueError("PEPPERPY_API_KEY environment variable is not set")

    config = LLMConfig(
        api_key=api_key,
        model=os.getenv("PEPPERPY_MODEL", "google/gemini-2.0-flash-exp:free"),
        provider=os.getenv("PEPPERPY_PROVIDER", "openrouter"),
    )
    
    llm = OpenRouterLLM(config)
    await llm.initialize()

    try:
        # Generate text
        prompt = "Write a haiku about programming"
        print(f"\nGenerating text for prompt: {prompt}")
        
        response = await llm.generate(prompt)
        print(f"\nGenerated text: {response.text}")
        print(f"Tokens used: {response.tokens_used}")
        print(f"Model used: {response.model}")

    finally:
        await llm.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 