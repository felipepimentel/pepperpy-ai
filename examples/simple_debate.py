"""Simple example demonstrating agent debate functionality."""

import asyncio
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

import aiohttp
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


@dataclass
class LLMConfig:
    """LLM configuration."""

    api_key: str
    model: str
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
        self.last_request_time = 0.0
        self.min_request_interval = 2.0  # Minimum seconds between requests

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession(
            base_url="https://openrouter.ai/",
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

        # Rate limiting
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

        data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        print(f"\nSending request to OpenRouter API...")
        print(f"Model: {self.config.model}")
        print(f"Prompt: {prompt[:100]}...")

        async with self.session.post("api/v1/chat/completions", json=data) as response:
            if response.status != 200:
                text = await response.text()
                if response.status == 429:  # Rate limit
                    print("Rate limit hit, waiting before retry...")
                    await asyncio.sleep(5)  # Wait 5 seconds
                    return await self.generate(prompt)  # Retry
                raise Exception(f"API request failed ({response.status}): {text}")

            result = await response.json()
            if "error" in result:
                if "code" in result["error"] and result["error"]["code"] == 429:
                    print("Rate limit hit, waiting before retry...")
                    await asyncio.sleep(5)  # Wait 5 seconds
                    return await self.generate(prompt)  # Retry
                raise Exception(f"API error: {json.dumps(result['error'], indent=2)}")

            print(f"Raw response: {json.dumps(result, indent=2)}")

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


class BaseAgent(ABC):
    """Base class for agents."""

    @abstractmethod
    async def process(self, input_text: str) -> str:
        """Process input and generate response."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class DebateAgent(BaseAgent):
    """Agent that can participate in a debate."""

    def __init__(self, name: str, perspective: str, llm: OpenRouterLLM) -> None:
        """Initialize debate agent.
        
        Args:
            name: Agent name
            perspective: Agent's debate perspective/stance
            llm: Language model for the agent
        """
        self.name = name
        self.perspective = perspective
        self.llm = llm
        self.debate_history: list[str] = []

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response
        """
        prompt = (
            f"You are {self.name}, with the following perspective: {self.perspective}\n"
            f"Previous debate points:\n"
            + "\n".join(self.debate_history[-3:])  # Show last 3 points for context
            + f"\n\nRespond to this argument: {input_text}\n"
            "Keep your response focused, civil, and under 100 words."
        )
        
        response = await self.llm.generate(prompt)
        self.debate_history.append(f"{self.name}: {response.text}")
        return response.text

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.llm.cleanup()


class ConsensusBuilder(BaseAgent):
    """Agent that builds consensus from a debate."""

    def __init__(self, name: str, llm: OpenRouterLLM) -> None:
        """Initialize consensus builder.
        
        Args:
            name: Agent name
            llm: Language model for the agent
        """
        self.name = name
        self.llm = llm

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response
        """
        prompt = (
            "As an impartial mediator, analyze the following debate and generate a "
            "balanced consensus that acknowledges the key points from both sides:\n\n"
            + input_text
            + "\n\nConsensus summary:"
        )
        
        response = await self.llm.generate(prompt)
        return response.text

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.llm.cleanup()


async def main() -> None:
    """Run the debate example."""
    # Get API key from environment
    api_key = os.getenv("PEPPERPY_API_KEY")
    if not api_key:
        raise ValueError("PEPPERPY_API_KEY environment variable is not set")

    # Initialize LLM configuration
    llm_config = LLMConfig(
        api_key=api_key,
        model=os.getenv("PEPPERPY_MODEL", "anthropic/claude-2"),  # Use Claude instead of Gemini
    )

    # Create LLMs for each agent
    llm1 = OpenRouterLLM(llm_config)
    llm2 = OpenRouterLLM(llm_config)
    llm3 = OpenRouterLLM(llm_config)

    await llm1.initialize()
    await llm2.initialize()
    await llm3.initialize()

    try:
        # Create debate agents
        optimist = DebateAgent(
            name="Optimist",
            perspective="You believe AI will greatly benefit humanity by solving major challenges",
            llm=llm1,
        )
        
        pragmatist = DebateAgent(
            name="Pragmatist",
            perspective="You believe AI needs careful regulation and gradual implementation",
            llm=llm2,
        )
        
        mediator = ConsensusBuilder(
            name="Mediator",
            llm=llm3,
        )

        # Start the debate
        print("\n=== Starting AI Impact Debate ===\n")
        
        # Initial argument
        initial_prompt = "What will be the impact of AI on society in the next decade?"
        
        # First round
        print("Round 1:")
        optimist_response = await optimist.process(initial_prompt)
        print(f"\nOptimist: {optimist_response}")
        
        pragmatist_response = await pragmatist.process(optimist_response)
        print(f"\nPragmatist: {pragmatist_response}")

        # Second round
        print("\nRound 2:")
        optimist_response = await optimist.process(pragmatist_response)
        print(f"\nOptimist: {optimist_response}")
        
        pragmatist_response = await pragmatist.process(optimist_response)
        print(f"\nPragmatist: {pragmatist_response}")

        # Generate consensus
        print("\n=== Generating Consensus ===\n")
        consensus = await mediator.process("\n".join(optimist.debate_history))
        print(f"Consensus Summary:\n{consensus}")

    finally:
        # Cleanup
        await optimist.cleanup()
        await pragmatist.cleanup()
        await mediator.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 