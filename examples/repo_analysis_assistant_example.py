"""Repository Analysis Assistant Example.

This example demonstrates a comprehensive code repository analysis assistant that:
1. Analyzes repository structure and organization
2. Evaluates code quality and maintainability
3. Identifies issues and recommends improvements
4. Generates documentation and diagrams
5. Performs security vulnerability scanning
6. Provides refactoring suggestions
7. Analyzes test coverage and quality
8. Allows interaction with the repository through natural language
"""

import asyncio
import sys

from pepperpy.core.base import PepperPy


async def main():
    """Run the example."""
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"

    # Create assistant using fluent interface
    async with PepperPy.create() as pepper:
        assistant = (
            pepper.create_assistant("repo-analyzer")
            .with_llm()
            .with_rag(
                collection_name="repo_analysis", persist_directory=".pepperpy/chroma"
            )
            .with_github()
            .build()
        )

        try:
            # Analyze repository
            await assistant.analyze_repository(repo_url)

            # Interactive mode
            if "--interactive" in sys.argv:
                while True:
                    question = input("Ask a question (or 'exit' to quit): ")
                    if question.lower() == "exit":
                        break

                    answer = await assistant.ask(question)
                    if answer:
                        print(f"\nAnswer: {answer}\n")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
