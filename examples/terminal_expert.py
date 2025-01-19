"""Example demonstrating terminal expert agent."""

import asyncio
import os

from dotenv import load_dotenv

from pepperpy.agents.terminal_agent import TerminalAgent, TerminalAgentConfig
from pepperpy.llms.huggingface import HuggingFaceLLM, LLMConfig
from pepperpy.tools.functions.terminal import TerminalTool


# Load environment variables
load_dotenv()


async def main() -> None:
    """Run the terminal expert example."""
    # Initialize LLM configuration
    llm_config = LLMConfig(
        model_name=os.getenv("PEPPERPY_MODEL", "anthropic/claude-2"),
        model_kwargs={
            "api_key": os.getenv("PEPPERPY_API_KEY", ""),
            "provider": os.getenv("PEPPERPY_PROVIDER", "openrouter"),
        },
    )

    # Create LLM and tools
    llm = HuggingFaceLLM(llm_config)
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