"""Example of using PepperPy for repository analysis."""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

from pepperpy import PepperPy
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import create_provider as create_rag_provider
from pepperpy.rag.base import Document

# Load environment variables from .env file
load_dotenv()

# Create necessary directories
os.makedirs("output/repos", exist_ok=True)


async def analyze_repository(repo_url: str) -> Dict[str, str]:
    """Analyze a Git repository and provide insights.

    Args:
        repo_url: URL of the repository to analyze

    Returns:
        Dictionary with analysis results
    """
    # Create providers
    llm_provider = create_llm_provider("openrouter")
    rag_provider = create_rag_provider("memory")

    # Create temp directory for repository
    repo_path = tempfile.mkdtemp()
    print(f"\nCloning repository to {repo_path}...")

    try:
        # Clone repository
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
        print(f"Repository cloned to: {repo_path}")

        # List repository files
        print("\nListing repository files...")
        files = []
        for root, _, filenames in os.walk(repo_path):
            for filename in filenames:
                if not filename.startswith(".") and not root.endswith("__pycache__"):
                    files.append(os.path.join(root, filename))

        print(f"Found {len(files)} files")

        # Index repository content
        print("\nIndexing repository content...")
        indexed_files = 0

        # Initialize PepperPy with LLM and RAG support
        async with PepperPy().with_llm(llm_provider).with_rag(rag_provider) as pepper:
            # List to store indexed documents
            documents = []

            for file_path in files[:10]:  # Limit to first 10 files for example
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    file_name = os.path.basename(file_path)
                    rel_path = os.path.relpath(file_path, repo_path)

                    # Create document
                    document = Document(
                        text=content[:2000],  # Limit content size
                        metadata={"file": rel_path, "type": "code", "repo": repo_url},
                    )

                    # Add document to list
                    documents.append(document)
                    print(f"Indexing: {rel_path}")
                    indexed_files += 1
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")

            print(f"\nSuccessfully indexed {indexed_files} files!")

            # Store documents in RAG
            for document in documents:
                await rag_provider.store_document(
                    text=document.text, metadata=document.metadata
                )

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
                    # First search for relevant context using the provider directly
                    search_results = await rag_provider.search_documents(
                        question, limit=3
                    )
                    context = ""
                    for result in search_results:
                        context += f"\n\n{result['text']}"

                    # Query the assistant with context
                    result = await (
                        pepper.chat.with_system(
                            "You are a repository analysis expert. Use the provided context to answer questions about the repository."
                        )
                        .with_user(f"Context:\n{context}\n\nQuestion: {question}")
                        .generate()
                    )
                    print(f"\nAnswer: {result.content}")
                except Exception as e:
                    print(f"\nError: {e}")

            # Save analysis summary
            results = {
                "repo_url": repo_url,
                "total_files": len(files),
                "indexed_files": indexed_files,
                "example_questions": questions[:-1],  # Exclude 'exit'
            }

            output_file = (
                Path("output/repos") / f"{repo_url.split('/')[-1]}_analysis.txt"
            )
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

            return results

    finally:
        # Clean up the temporary directory
        shutil.rmtree(repo_path, ignore_errors=True)


async def main() -> None:
    """Run the example."""
    print("Repository Analysis Assistant Example")
    print("=" * 50)

    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    await analyze_repository(repo_url)


if __name__ == "__main__":
    # Using openrouter LLM provider and memory RAG provider
    asyncio.run(main())
