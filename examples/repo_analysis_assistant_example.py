"""Example of using PepperPy for repository analysis.

This example demonstrates how to use PepperPy to analyze
GitHub repositories and answer questions about them.
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from pepperpy import PepperPy

# Create necessary output directory
os.makedirs("output/repos", exist_ok=True)


async def main():
    """Run the repository analysis example."""
    print("Repository Analysis Assistant Example")
    print("=" * 50)

    # Repository to analyze
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"

    # Create temp directory for repository
    repo_path = tempfile.mkdtemp()
    print(f"\nCloning repository to {repo_path}...")

    try:
        # Initialize PepperPy
        app = PepperPy()
        await app.initialize()

        try:
            # Clone repository
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)
            print(f"Repository cloned to: {repo_path}")

            # List repository files
            print("\nListing repository files...")
            files = []
            for root, _, filenames in os.walk(repo_path):
                for filename in filenames:
                    if not filename.startswith(".") and not root.endswith(
                        "__pycache__"
                    ):
                        files.append(os.path.join(root, filename))

            print(f"Found {len(files)} files")

            # Index repository content
            print("\nIndexing repository content...")
            indexed_files = 0

            # Process the repository files (limit to first 10 for example)
            for file_path in files[:10]:
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    rel_path = os.path.relpath(file_path, repo_path)
                    print(f"Indexing: {rel_path}")

                    # Add file to knowledge base
                    await app.execute(
                        query="Index repository file",
                        context={
                            "file_path": rel_path,
                            "content": content[:2000],  # Limit content size
                            "metadata": {"type": "code", "repo": repo_url},
                        },
                    )

                    indexed_files += 1
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")

            print(f"\nSuccessfully indexed {indexed_files} files!")

            # Answer questions about the repository
            questions = [
                "What is the main purpose of this repository?",
                "What are the main files in the project?",
                "How is the code structured?",
            ]

            # Process each question
            print("\nAnalyzing repository with common questions:")
            for question in questions:
                print(f"\nQuestion: {question}")

                # Get answer from PepperPy
                answer = await app.execute(
                    query=question, context={"repo_url": repo_url}
                )

                print(f"Answer: {answer}")

            # Save analysis summary
            output_file = (
                Path("output/repos") / f"{repo_url.split('/')[-1]}_analysis.txt"
            )
            with open(output_file, "w") as f:
                f.write(f"Repository Analysis: {repo_url}\n")
                f.write(f"Total files: {len(files)}\n")
                f.write(f"Indexed files: {indexed_files}\n")
                f.write("\nAnswers to common questions:\n")
                for i, question in enumerate(questions):
                    f.write(f"{i + 1}. {question}\n")

            print(f"\nAnalysis summary saved to: {output_file}")

        finally:
            # Clean up resources
            await app.cleanup()

    finally:
        # Clean up the temporary directory
        shutil.rmtree(repo_path, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
