"""Example demonstrating agent debate functionality."""

import asyncio
import os
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from pydantic import BaseModel

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig
from pepperpy.capabilities.tools.tool import Tool, ToolResult


# Load environment variables
load_dotenv()


class DebateAgentConfig(BaseModel):
    """Configuration for debate agent."""

    name: str
    perspective: str
    llm: HuggingFaceProvider


class DebateAgent(BaseAgent):
    """Agent that can participate in a debate."""

    def __init__(self, config: DebateAgentConfig) -> None:
        """Initialize debate agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.debate_history: list[str] = []

    @classmethod
    def validate_config(cls, config: Any) -> bool:
        """Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return (
            isinstance(config, DebateAgentConfig)
            and isinstance(config.name, str)
            and isinstance(config.perspective, str)
            and isinstance(config.llm, HuggingFaceProvider)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response
        """
        return await self.respond_to_argument(input_text)

    async def process_stream(self, input_text: str) -> AsyncIterator[str]:
        """Process input and generate streaming response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response chunks
        """
        async for chunk in self.config.llm.generate_stream(input_text):
            yield chunk

    async def respond_to_argument(self, argument: str) -> str:
        """Generate a response to an argument.
        
        Args:
            argument: The argument to respond to
            
        Returns:
            Response to the argument
        """
        prompt = (
            f"You are {self.config.name}, with the following perspective: {self.config.perspective}\n"
            f"Previous debate points:\n"
            + "\n".join(self.debate_history[-3:])  # Show last 3 points for context
            + f"\n\nRespond to this argument: {argument}\n"
            "Keep your response focused, civil, and under 100 words."
        )
        
        response = await self.config.llm.generate(prompt)
        self.debate_history.append(f"{self.config.name}: {response.text}")
        return response.text

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup()


class ConsensusBuilderConfig(BaseModel):
    """Configuration for consensus builder agent."""

    name: str
    llm: HuggingFaceProvider


class ConsensusBuilder(BaseAgent):
    """Agent that builds consensus from a debate."""

    def __init__(self, config: ConsensusBuilderConfig) -> None:
        """Initialize consensus builder.
        
        Args:
            config: Agent configuration
        """
        self.config = config

    @classmethod
    def validate_config(cls, config: Any) -> bool:
        """Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return (
            isinstance(config, ConsensusBuilderConfig)
            and isinstance(config.name, str)
            and isinstance(config.llm, HuggingFaceProvider)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response
        """
        return await self.generate_consensus(input_text.split("\n"))

    async def process_stream(self, input_text: str) -> AsyncIterator[str]:
        """Process input and generate streaming response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response chunks
        """
        async for chunk in self.config.llm.generate_stream(input_text):
            yield chunk

    async def generate_consensus(self, debate_history: list[str]) -> str:
        """Generate a consensus summary from debate history.
        
        Args:
            debate_history: List of debate points
            
        Returns:
            Consensus summary
        """
        prompt = (
            "As an impartial mediator, analyze the following debate and generate a "
            "balanced consensus that acknowledges the key points from both sides:\n\n"
            + "\n".join(debate_history)
            + "\n\nConsensus summary:"
        )
        
        response = await self.config.llm.generate(prompt)
        return response.text

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup()


async def main() -> None:
    """Run the debate example."""
    # Initialize LLM configuration
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise ValueError("HUGGINGFACE_API_KEY environment variable is required")

    llm_config = LLMConfig(
        api_key=api_key,
        model="mistralai/Mistral-7B-Instruct-v0.1",
        base_url="https://api-inference.huggingface.co/models",
        temperature=0.7,
        max_tokens=1000
    )

    # Create LLMs for each agent
    llm1 = HuggingFaceProvider(llm_config.to_dict())
    llm2 = HuggingFaceProvider(llm_config.to_dict())
    llm3 = HuggingFaceProvider(llm_config.to_dict())

    try:
        # Create debate agents
        optimist = DebateAgent(
            config=DebateAgentConfig(
                name="Optimist",
                perspective="You believe AI will greatly benefit humanity by solving major challenges",
                llm=llm1,
            )
        )
        
        pragmatist = DebateAgent(
            config=DebateAgentConfig(
                name="Pragmatist",
                perspective="You believe AI needs careful regulation and gradual implementation",
                llm=llm2,
            )
        )
        
        mediator = ConsensusBuilder(
            config=ConsensusBuilderConfig(
                name="Mediator",
                llm=llm3,
            )
        )

        # Initialize agents
        await optimist.initialize()
        await pragmatist.initialize()
        await mediator.initialize()

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