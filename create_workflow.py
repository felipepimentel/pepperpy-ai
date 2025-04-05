#!/usr/bin/env python3

import asyncio

from plugins.workflow.repository_analyzer.provider import RepositoryAnalyzerAdapter


async def main():
    # Create the workflow provider directly
    workflow = RepositoryAnalyzerAdapter()

    # Initialize the provider
    await workflow.initialize()

    try:
        # Create input data with minimal requirements
        input_data = {
            "task": "analyze_structure",  # Simpler analysis that doesn't need LLM
            "repository_path": ".",
            "topic": "repository analysis",  # Added for ContentGeneratorWorkflow compatibility
        }

        # Execute the workflow
        result = await workflow.execute(input_data)

        # Print the result
        print("\nWorkflow execution result:")
        print(result)

    finally:
        # Clean up
        await workflow.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
