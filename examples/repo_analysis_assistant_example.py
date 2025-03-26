"""Example of using the repository analysis recipe."""

import asyncio

from pepperpy.core.base import PepperPy
from pepperpy.workflow.recipes.code.repository import RepositoryAnalysisRecipe


async def main():
    """Run the example."""
    try:
        # Create PepperPy instance - all configuration is handled by the framework
        pepperpy = (
            PepperPy.create()
            .with_llm()  # Uses PEPPERPY_LLM__ config
            .with_rag()  # Uses PEPPERPY_RAG__ config
            .with_github()  # Uses PEPPERPY_TOOLS__ config
            .build()
        )

        # Create recipe
        recipe = RepositoryAnalysisRecipe(
            name="repo-analyzer",
            llm=pepperpy.llm,
            rag=pepperpy.rag,
            repository=pepperpy.github,
        )

        # Analyze repository
        repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
        await recipe.analyze(repo_url)

        # Interactive mode
        print("\nEnter your questions about the repository (type 'exit' to quit):")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() == "exit":
                break

            answer = await recipe.ask(question)
            if answer:
                print(f"\nAnswer: {answer}")
            else:
                print("\nError: Could not generate answer")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
