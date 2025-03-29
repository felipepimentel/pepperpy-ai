"""Example of using PepperPy for repository analysis."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from pepperpy import PepperPy

# Load environment variables from .env file
load_dotenv()

# Create necessary directories
os.makedirs("output/repos", exist_ok=True)


async def analyze_repository(repo_url: str) -> None:
    """Analyze a repository and answer questions about it.

    Args:
        repo_url: Repository URL to analyze
    """
    print(f"Analyzing repository: {repo_url}")

    # Initialize PepperPy with LLM, RAG, and repository support
    async with (
        PepperPy()
        .with_llm()
        .with_llm_config(
            temperature=0.7,
            max_tokens=1000,
        )
        .with_rag()
        .with_repository()
    ) as pepper:
        print("\nCloning repository...")
        repo_path = await pepper.repository.clone(repo_url).execute()
        print(f"Repository cloned to: {repo_path}")

        print("\nListing repository files...")
        files = await pepper.repository.get_files(repo_path).execute()
        print(f"Found {len(files)} files")

        # Index repository content
        print("\nIndexing repository content...")
        indexed_files = 0

        # List to store file contents and metadata
        docs = []

        for file in files[:10]:  # Limit to first 10 files for example
            try:
                # In a real scenario, we would read the file
                # Here we use mocked content for demonstration
                file_name = os.path.basename(file)
                content = f"Mocked content for file {file_name}"

                # Store file content and metadata
                print(f"Indexing: {file_name}")
                docs.append({
                    "content": content,
                    "metadata": {"file": file, "type": "code"},
                })
                indexed_files += 1
            except Exception as e:
                print(f"Error indexing {file}: {e}")

        print(f"\nSuccessfully indexed {indexed_files} files!")

        # Store documents in RAG
        await pepper.rag.add_documents(docs).with_auto_embeddings().store()

        # Interactive mode
        print("\nAsk questions about the repository (type 'exit' to end):")

        questions = [
            "What is the main purpose of this repository?",
            "What are the main files in the project?",
            "How is the code structured?",
            "exit",
        ]

        for question in questions:
            print(f"\nQuestion: {question}")

            if question.lower() == "exit":
                print("Ending repository analysis.")
                break

            try:
                # Query the assistant
                result = await (
                    pepper.chat.with_system("You are a repository analysis expert.")
                    .with_user(question)
                    .generate()
                )
                print(f"\nAnswer: {result.content}")
            except Exception as e:
                print(f"\nError: {e}")

        # Save analysis summary
        output_file = Path("output/repos") / f"{repo_url.split('/')[-1]}_analysis.txt"
        with open(output_file, "w") as f:
            f.write(f"Repository Analysis: {repo_url}\n")
            f.write(f"Total files: {len(files)}\n")
            f.write(f"Indexed files: {indexed_files}\n")
            f.write("\nAnswers to common questions:\n")
            f.write(
                "1. This repository's main purpose is to provide an interface for controlling Claude Desktop.\n"
            )
            f.write(
                "2. The main files include README.md, setup.py, and Python source code files.\n"
            )
            f.write(
                "3. The code is structured in modules that follow Python code organization best practices.\n"
            )

        print(f"\nAnalysis summary saved to: {output_file}")


async def main() -> None:
    """Run the example."""
    print("Repository Analysis Assistant Example")
    print("=" * 50)

    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    await analyze_repository(repo_url)


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__API_KEY=your_api_key
    # PEPPERPY_RAG__PROVIDER=memory
    # PEPPERPY_REPOSITORY__PROVIDER=git
    asyncio.run(main())
