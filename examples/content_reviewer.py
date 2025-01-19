"""Example demonstrating content review agent."""

import asyncio
import os

from dotenv import load_dotenv

from pepperpy.agents.review_agent import ReviewAgent, ReviewAgentConfig
from pepperpy.llms.huggingface import HuggingFaceLLM, LLMConfig
from pepperpy.tools.functions.document_loader import DocumentLoaderTool


# Load environment variables
load_dotenv()


# Example review criteria
REVIEW_CRITERIA = {
    "clarity": "Is the content clear and well-organized?",
    "completeness": "Does it cover all necessary information?",
    "accuracy": "Is the information accurate and up-to-date?",
    "style": "Is the writing style appropriate for the audience?",
    "actionability": "Are there clear next steps or takeaways?",
}


async def main() -> None:
    """Run the content review example."""
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
    document_loader = DocumentLoaderTool()

    try:
        # Create review agent
        agent = ReviewAgent(
            config=ReviewAgentConfig(
                llm=llm,
                document_loader=document_loader,
                review_criteria=REVIEW_CRITERIA,
            )
        )

        # Initialize agent
        await agent.initialize()

        print("\n=== Content Review Agent ===\n")
        
        # Example files to review
        files = [
            "README.md",
            "TECHNICAL_SPECS.md",
            "examples/content_reviewer.py",
        ]
        
        for file in files:
            print(f"\nReviewing: {file}")
            print("-" * 50)
            result = await agent.process(file)
            print(result)
            print()

    finally:
        # Cleanup
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 