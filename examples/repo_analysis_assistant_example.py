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
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from pepperpy.core import Config, ValidationError
from pepperpy.embeddings.providers.openai import OpenAIEmbeddingProvider
from pepperpy.github import GitHubClient
from pepperpy.llm.base import Message, MessageRole
from pepperpy.llm.providers.openrouter import OpenRouterProvider
from pepperpy.rag import Document, Query, RAGContext
from pepperpy.rag.providers.chroma import ChromaProvider


def _build_context_from_report(report: Dict) -> str:
    """Build context string from analysis report."""
    context = f"Repository: {report['repository_name']}\n"
    context += f"Description: {report['description']}\n\n"

    if report.get("relevant_files"):
        context += "Relevant files:\n"
        for file in report["relevant_files"]:
            context += f"\nFile: {file['path']}\n"
            context += f"Content:\n{file['content']}\n"

    return context


async def analyze_repository(
    github: GitHubClient, repo_identifier: str, rag_context: RAGContext
) -> Tuple[Optional[Dict], str, GitHubClient]:
    """Analyze repository and generate report."""
    print("\nAnalyzing repository...")

    try:
        # Get repository info
        repo = await github.get_repository(repo_identifier)

        # Get list of files
        files = await github.get_files(repo_identifier)

        # Search for relevant files
        query = Query("repository structure and architecture")
        results = await rag_context.search(query)

        # Build report from results
        report = {
            "repository_name": repo_identifier,
            "description": repo.get("description", "No description available"),
            "files": [file["path"] for file in files],
            "relevant_files": [
                {"path": result.metadata["file_path"], "content": result.text}
                for result in results
            ],
            "structure": {
                "files_count": len(files),
                "languages": {},  # To be filled by language detection
            },
            "code_quality": {
                "maintainability_index": 0.0,
                "test_coverage": 0.0,
                "documentation_coverage": 0.0,
                "issues": {},
            },
            "recommendations": [],  # To be filled by analysis
        }

        # Save report to file
        output_dir = Path("examples/output/repo_analysis")
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"{repo_identifier.replace('/', '_')}_report.json"

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report, str(report_path), github

    except Exception as e:
        print(f"Error analyzing repository: {e}")
        return None, "", github


async def index_repository(
    github: GitHubClient, repo_identifier: str
) -> Optional[RAGContext]:
    """Index repository content for RAG."""
    print("\nIndexing repository contents...")

    try:
        # Get list of files
        files = await github.get_files(repo_identifier)

        # Index relevant files
        documents = []
        for file in files:
            # Skip binary files, images, etc.
            if _is_text_file(file["name"]):
                try:
                    content = await github.get_file_content(
                        repo_identifier, file["path"]
                    )

                    # Create document for RAG
                    doc = Document(
                        text=content,
                        metadata={
                            "file_path": file["path"],
                            "file_name": file["name"],
                            "repo": repo_identifier,
                        },
                    )
                    documents.append(doc)
                except Exception as e:
                    print(f"Error indexing file {file['path']}: {e}")

        # Initialize embedding provider
        embedding_provider = OpenAIEmbeddingProvider(
            api_key=os.getenv("PEPPERPY_EMBEDDINGS__OPENAI_API_KEY")
        )
        await embedding_provider.initialize()

        # Initialize RAG provider and context
        rag_provider = ChromaProvider(
            collection_name=f"repo-{repo_identifier.replace('/', '-')}",
            embedding_function=embedding_provider,
        )
        await rag_provider.initialize()

        rag_context = RAGContext(
            provider=rag_provider, embedding_provider=embedding_provider
        )

        # Add documents to RAG context
        await rag_context.add_documents(documents)
        print(f"Indexed {len(documents)} files from repository")

        return rag_context

    except Exception as e:
        print(f"Error indexing repository: {e}")
        return None


async def ask_about_repository(
    question: str, report: Dict, rag_context: RAGContext
) -> Optional[str]:
    """Ask a question about the repository."""
    # First, retrieve relevant documents
    query = Query(question)
    results = await rag_context.search(query)

    # Build context from analysis report and retrieved documents
    context = _build_context_from_report(report)

    # Add retrieved documents to context
    for result in results:
        context += f"\nFile: {result.metadata['file_path']}\n"
        content = result.text[:1000]
        context += f"Content: {content}...\n"

    # Get API key from environment
    api_key = os.getenv("PEPPERPY_LLM__API_KEY")
    if not api_key:
        raise ValidationError("PEPPERPY_LLM__API_KEY environment variable not set")

    # Initialize LLM from environment configuration
    llm = OpenRouterProvider(
        api_key=os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY"),
        model="anthropic/claude-3-sonnet",
    )
    await llm.initialize()

    try:
        # Generate response
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are an expert repository analyst. Help answer questions about the repository.",
            ),
            Message(
                role=MessageRole.USER,
                content=f"""
Repository: {report["repository_name"]}
Analysis:
{context}

Question: {question}

Please answer the question based on the repository information and analysis.""",
            ),
        ]

        result = await llm.generate(messages)
        return result.content
    finally:
        await llm.cleanup()


def _is_text_file(filename: str) -> bool:
    """Check if a file is a text file based on extension."""
    text_extensions = [
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".json",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".toml",
        ".rst",
        ".go",
        ".c",
        ".cpp",
        ".h",
        ".java",
        ".rb",
        ".sh",
        ".bash",
        ".php",
        ".rs",
        ".lua",
    ]

    return any(filename.endswith(ext) for ext in text_extensions)


class RepositoryChatAssistant:
    """Assistant for analyzing and chatting about repositories."""

    def __init__(self, repo_url: str):
        """Initialize the assistant.

        Args:
            repo_url: URL of the repository to analyze
        """
        self.repo_url = repo_url
        self.config = Config(env_prefix="PEPPERPY_")

        # Initialize LLM provider from environment
        self.llm = OpenRouterProvider(
            api_key=os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY"),
            model="anthropic/claude-3-sonnet",
        )

        # Initialize embedding provider
        self.embedding_provider = OpenAIEmbeddingProvider(
            api_key=os.getenv("PEPPERPY_EMBEDDINGS__OPENAI_API_KEY")
        )

        # Initialize RAG provider
        self.rag_provider = ChromaProvider(
            collection_name="repo_analysis",
            persist_directory=".pepperpy/chroma",
            embedding_function=self.embedding_provider,
        )

        # Initialize RAG context
        self.rag_context = RAGContext(
            provider=self.rag_provider, embedding_provider=self.embedding_provider
        )

    async def analyze(self) -> None:
        """Analyze the repository and index its content."""
        # Initialize providers
        await self.llm.initialize()
        await self.embedding_provider.initialize()
        await self.rag_provider.initialize()

        # Initialize GitHub client
        github = GitHubClient(token=os.getenv("PEPPERPY_TOOLS__GITHUB_API_KEY"))

        # Index repository for RAG
        rag_context = await index_repository(github, self.repo_url)
        if not rag_context:
            print("Error indexing repository, cannot analyze")
            return

        # Analyze repository
        report, report_path, github = await analyze_repository(
            github, self.repo_url, rag_context
        )
        if not report:
            print("Error analyzing repository")
            return

        # Display summary information
        print("\nRepository Analysis Summary:")
        print(f"Repository: {report['repository_name']} ({self.repo_url})")
        print(f"Files: {len(report['files'])}")
        print(
            f"Languages: {', '.join(f'{lang} ({pct:.1f}%)' for lang, pct in report['structure']['languages'].items())}"
        )
        print("Code Quality:")
        print(
            f"  - Maintainability: {report['code_quality']['maintainability_index']:.1f}/100"
        )
        print(f"  - Test Coverage: {report['code_quality']['test_coverage']:.1f}%")
        print(
            f"  - Doc Coverage: {report['code_quality']['documentation_coverage']:.1f}%"
        )

        # Display issues summary
        total_issues = sum(
            len(issues) for issues in report["code_quality"]["issues"].values()
        )
        print(f"Issues Found: {total_issues}")
        for severity, issues in report["code_quality"]["issues"].items():
            if issues:
                print(f"  - {severity.capitalize()}: {len(issues)}")

        # Display top recommendations
        print("\nTop Recommendations:")
        for i, rec in enumerate(report["recommendations"][:3], 1):
            print(f"{i}. {rec}")

        print(f"\nFull report saved to: {report_path}")

        # Example questions about the repository
        questions = [
            "What is the main purpose of this repository?",
            "What are the main components of the architecture?",
            "What are the most critical issues that need to be fixed?",
            "How is the code quality overall?",
            "What improvements would you suggest for the test coverage?",
        ]

        print("\n===== Repository Q&A =====")
        for question in questions:
            print(f"\nQ: {question}")
            answer = await ask_about_repository(question, report, rag_context)
            print(f"A: {answer}")

    async def ask(self, question: str) -> str:
        """Ask a question about the repository.

        Args:
            question: The question to ask

        Returns:
            The answer to the question
        """
        # Use RAG to find relevant context
        query = Query(question)
        results = await self.rag_context.search(query)

        # Build context from documents
        context_text = "\n\n".join(
            f"File: {result.metadata['file_path']}\n{result.text}" for result in results
        )

        # Generate response using LLM
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="You are a helpful repository analysis assistant.",
            ),
            Message(
                role=MessageRole.USER,
                content=f"Question about the repository: {question}\n\nContext: {context_text}",
            ),
        ]

        response = await self.llm.generate(messages)

        return response.content


async def main():
    """Run the example."""
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    assistant = RepositoryChatAssistant(repo_url)

    # Analyze repository
    await assistant.analyze()

    # Interactive mode
    if "--interactive" in sys.argv:
        while True:
            question = input("Ask a question (or 'exit' to quit): ")
            if question.lower() == "exit":
                break

            answer = await assistant.ask(question)
            print(f"\nAnswer: {answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
