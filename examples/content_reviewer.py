"""Example demonstrating content review agent."""

import asyncio
import os

from dotenv import load_dotenv

from pepperpy.agents.review_agent import ReviewAgent, ReviewAgentConfig
from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig
from pepperpy.capabilities.tools.document_loader import DocumentLoaderTool


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
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise ValueError("HUGGINGFACE_API_KEY environment variable is required")

    llm_config = LLMConfig(
        api_key=api_key,
        model="anthropic/claude-2",
        base_url="https://api-inference.huggingface.co/models",
        temperature=0.7,
        max_tokens=1000
    )

    # Create LLM and tools
    llm = HuggingFaceProvider(llm_config.to_dict())
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