"""Example of using PepperPy for repository analysis."""

import asyncio

from pepperpy import PepperPy


async def analyze_repository(repo_url: str) -> None:
    """Analyze a repository and answer questions about it.

    Args:
        repo_url: Repository URL to analyze
    """
    async with PepperPy().with_llm().with_rag().with_repository() as assistant:
        # Index repository contents
        repo = assistant.repository
        await repo.clone(repo_url)

        files = await repo.list_files()
        for file in files:
            content = await repo.read_file(file)
            await assistant.learn(content, metadata={"file": file})

        # Interactive mode
        print("\nEnter your questions about the repository (type 'exit' to quit):")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() == "exit":
                break

            try:
                answer = await assistant.ask(question)
                print(f"\nAnswer: {answer.content}")
            except Exception as e:
                print(f"\nError: {e}")


async def main() -> None:
    """Run the example."""
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    await analyze_repository(repo_url)


if __name__ == "__main__":
    asyncio.run(main())
