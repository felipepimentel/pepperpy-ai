"""Repository analysis workflow recipe."""

from typing import Dict, Optional

from pepperpy.llm.base import Message, MessageRole
from pepperpy.llm.component import LLMComponent
from pepperpy.rag import Document, Query
from pepperpy.rag.component import RAGComponent
from pepperpy.tools.repository.providers.github import GitHubProvider
from pepperpy.workflow.base import Workflow


class RepositoryAnalysisRecipe(Workflow):
    """Recipe for analyzing and interacting with code repositories.

    This recipe combines LLM, RAG, and repository tools to provide:
    - Repository analysis and indexing
    - Code search and understanding
    - Natural language Q&A about the codebase

    Example:
        >>> recipe = RepositoryAnalysisRecipe(
        ...     name="repo-analyzer",
        ...     llm=llm_component,
        ...     rag=rag_component,
        ...     repository=github_provider
        ... )
        >>> await recipe.analyze("https://github.com/user/repo")
        >>> answer = await recipe.ask("How is error handling implemented?")
    """

    def __init__(
        self,
        name: str,
        llm: LLMComponent,
        rag: RAGComponent,
        repository: GitHubProvider,
    ) -> None:
        """Initialize repository analysis recipe.

        Args:
            name: Recipe name
            llm: LLM component for text generation
            rag: RAG component for document storage and retrieval
            repository: Repository provider for accessing code
        """
        super().__init__()
        self.name = name
        self.llm = llm
        self.rag = rag
        self.repository = repository
        self._indexed = False

    async def analyze(self, repo_url: str) -> Dict:
        """Analyze a repository.

        Args:
            repo_url: Repository URL

        Returns:
            Analysis results including repository info, structure, and metrics
        """
        print(f"\nAnalyzing repository {repo_url}...")

        # Get repository info
        repo = await self.repository.get_repository(repo_url)
        if not repo:
            print("Error: Could not fetch repository info")
            return {
                "repository_name": repo_url,
                "error": "Could not fetch repository info",
            }

        files = await self.repository.get_files(repo_url)
        if not files:
            print("Error: Could not fetch repository files")
            return {
                "repository_name": repo_url,
                "error": "Could not fetch repository files",
            }

        # Index files
        documents = []
        for file in files:
            if self._is_text_file(file["name"]):
                try:
                    content = await self.repository.get_file_content(
                        repo_url, file["path"]
                    )
                    if content:
                        doc = Document(
                            text=content,
                            metadata={
                                "file_path": file["path"],
                                "file_name": file["name"],
                                "repo": repo_url,
                            },
                        )
                        documents.append(doc)
                except Exception as e:
                    print(f"Error indexing file {file['path']}: {e}")

        # Add documents to RAG
        await self.rag.add_documents(documents)
        self._indexed = True
        print(f"Indexed {len(documents)} files from repository")

        # Generate analysis
        query = Query("repository structure and architecture")
        results = await self.rag.search(query)
        if not results:
            results = []

        # Build report
        report = {
            "repository_name": repo_url,
            "description": repo.get("description", "No description available"),
            "files": [file["path"] for file in files],
            "relevant_files": [
                {
                    "path": getattr(result.metadata, "file_path", "unknown"),
                    "content": getattr(result, "text", ""),
                }
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

        # Display summary
        print("\nRepository Analysis Summary:")
        print(f"Repository: {report['repository_name']}")
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

        # Display issues
        total_issues = sum(
            len(issues) for issues in report["code_quality"]["issues"].values()
        )
        print(f"Issues Found: {total_issues}")
        for severity, issues in report["code_quality"]["issues"].items():
            if issues:
                print(f"  - {severity.capitalize()}: {len(issues)}")

        # Display recommendations
        print("\nTop Recommendations:")
        for i, rec in enumerate(report["recommendations"][:3], 1):
            print(f"{i}. {rec}")

        return report

    async def ask(self, question: str) -> Optional[str]:
        """Ask a question about the repository.

        Args:
            question: Question to ask

        Returns:
            Answer to the question or None if repository not analyzed
        """
        if not self._indexed:
            print("Repository not analyzed yet. Please run analyze() first.")
            return None

        # Get relevant context
        query = Query(question)
        results = await self.rag.search(query)
        if not results:
            results = []

        # Build context
        context = "\n\n".join(
            f"File: {getattr(result.metadata, 'file_path', 'unknown')}\n{getattr(result, 'text', '')}"
            for result in results
        )

        # Generate response
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=f"You are {self.name}, a helpful repository analysis assistant.",
            ),
            Message(
                role=MessageRole.USER,
                content=f"Question about the repository: {question}\n\nContext: {context}",
            ),
        ]

        try:
            response = await self.llm.generate(messages)
            if not response:
                return None
            return response.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return None

    def _is_text_file(self, filename: str) -> bool:
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
