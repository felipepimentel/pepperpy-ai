"""Example demonstrating terminal expert agent."""

import asyncio
import os

from dotenv import load_dotenv

from pepperpy.agents.terminal_agent import TerminalAgent, TerminalAgentConfig
from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig
from pepperpy.capabilities.tools.terminal import TerminalTool


# Load environment variables
load_dotenv()


async def main() -> None:
    """Run the terminal expert example."""
    # Initialize LLM configuration
    if not os.getenv("HUGGINGFACE_API_KEY"):
        raise ValueError("HUGGINGFACE_API_KEY environment variable is required")

    llm_config = LLMConfig(
        api_key=os.environ["HUGGINGFACE_API_KEY"],
        model="anthropic/claude-2",
        base_url="https://api-inference.huggingface.co/models"
    )

    # Create LLM and tools
    llm = HuggingFaceProvider(llm_config.to_dict())
    terminal_tool = TerminalTool()

    try:
        # Create terminal agent
        agent = TerminalAgent(
            config=TerminalAgentConfig(
                llm=llm,
                terminal_tool=terminal_tool,
            )
        )

        # Initialize agent
        await agent.initialize()

        print("\n=== Terminal Expert Agent ===\n")
        
        # Example commands
        commands = [
            "list files in the current directory",
            "show me the first 5 lines of README.md",
            "count the number of Python files in this directory",
            "show disk usage in human readable format",
        ]
        
        for cmd in commands:
            print(f"\nCommand: {cmd}")
            print("-" * 50)
            result = await agent.process(cmd)
            print(result)
            print()

    finally:
        # Cleanup
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 