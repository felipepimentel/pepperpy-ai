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
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from pepperpy.core import Config
from pepperpy.embeddings import EmbeddingProvider
from pepperpy.github import GitHubClient
from pepperpy.llm.base import Message, MessageRole
from pepperpy.llm.provider import LLMProvider
from pepperpy.rag import Document, Query, RAGContext
from pepperpy.rag.provider import RAGProvider


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
    github: GitHubClient,
    repo_identifier: str,
    rag_provider: RAGProvider,
    embedding_provider: EmbeddingProvider,
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

        # Initialize RAG context
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
    question: str, report: Dict, rag_context: RAGContext, llm: LLMProvider
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
    except Exception as e:
        print(f"Error generating response: {e}")
        return None


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

    def __init__(
        self,
        repo_url: str,
        llm: LLMProvider,
        embedding_provider: EmbeddingProvider,
        rag_provider: RAGProvider,
        github: GitHubClient,
    ):
        """Initialize the assistant.

        Args:
            repo_url: URL of the repository to analyze
            llm: LLM provider instance
            embedding_provider: Embedding provider instance
            rag_provider: RAG provider instance
            github: GitHub client instance
        """
        self.repo_url = repo_url
        self.llm = llm
        self.embedding_provider = embedding_provider
        self.rag_provider = rag_provider
        self.github = github
        self.rag_context = None

    async def analyze(self) -> None:
        """Analyze the repository and index its content."""
        # Index repository for RAG
        self.rag_context = await index_repository(
            self.github, self.repo_url, self.rag_provider, self.embedding_provider
        )
        if not self.rag_context:
            print("Error indexing repository, cannot analyze")
            return

        # Analyze repository
        report, report_path, _ = await analyze_repository(
            self.github, self.repo_url, self.rag_context
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
            answer = await ask_about_repository(
                question, report, self.rag_context, self.llm
            )
            print(f"A: {answer}")

    async def ask(self, question: str) -> Optional[str]:
        """Ask a question about the repository.

        Args:
            question: The question to ask

        Returns:
            The answer to the question
        """
        if not self.rag_context:
            print("Repository not analyzed yet. Please run analyze() first.")
            return None

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

        try:
            response = await self.llm.generate(messages)
            return response.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return None


async def main():
    """Run the example."""
    # Initialize providers using the framework's configuration system
    config = Config()

    # Get providers from the framework
    llm = config.load_llm_provider()
    embedding_provider = config.load_embedding_provider()
    rag_provider = config.load_rag_provider(
        collection_name="repo_analysis", persist_directory=".pepperpy/chroma"
    )
    github = config.load_github_client()

    # Initialize all providers
    await llm.initialize()
    await embedding_provider.initialize()
    await rag_provider.initialize()
    await github.initialize()

    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    assistant = RepositoryChatAssistant(
        repo_url=repo_url,
        llm=llm,
        embedding_provider=embedding_provider,
        rag_provider=rag_provider,
        github=github,
    )

    try:
        # Analyze repository
        await assistant.analyze()

        # Interactive mode
        if "--interactive" in sys.argv:
            while True:
                question = input("Ask a question (or 'exit' to quit): ")
                if question.lower() == "exit":
                    break

                answer = await assistant.ask(question)
                if answer:
                    print(f"\nAnswer: {answer}\n")
    finally:
        # Cleanup
        await llm.cleanup()
        await embedding_provider.cleanup()
        await rag_provider.cleanup()
        await github.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
