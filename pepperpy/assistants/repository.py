"""Repository assistant module."""

from typing import Optional

from pepperpy.core.base import BaseComponent
from pepperpy.github.component import GitHubComponent
from pepperpy.llm.base import Message, MessageRole
from pepperpy.llm.component import LLMComponent
from pepperpy.rag import Document, Query
from pepperpy.rag.component import RAGComponent


class RepositoryAssistant(BaseComponent):
    """Assistant for analyzing and chatting about repositories."""

    def __init__(
        self,
        name: str,
        llm: LLMComponent,
        rag: RAGComponent,
        github: GitHubComponent,
    ) -> None:
        """Initialize repository assistant.

        Args:
            name: Assistant name
            llm: LLM component
            rag: RAG component
            github: GitHub component
        """
        super().__init__()
        self.name = name
        self.llm = llm
        self.rag = rag
        self.github = github
        self._indexed = False

    async def analyze_repository(self, repo_url: str) -> None:
        """Analyze a repository.

        Args:
            repo_url: Repository URL
        """
        print(f"\nAnalyzing repository {repo_url}...")

        # Get repository info
        repo = await self.github.get_repository(repo_url)
        files = await self.github.get_files(repo_url)

        # Index files
        documents = []
        for file in files:
            if self._is_text_file(file["name"]):
                try:
                    content = await self.github.get_file_content(repo_url, file["path"])
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

        # Build report
        report = {
            "repository_name": repo_url,
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

    async def ask(self, question: str) -> Optional[str]:
        """Ask a question about the repository.

        Args:
            question: Question to ask

        Returns:
            Answer to the question
        """
        if not self._indexed:
            print("Repository not analyzed yet. Please run analyze_repository() first.")
            return None

        # Get relevant context
        query = Query(question)
        results = await self.rag.search(query)

        # Build context
        context = "\n\n".join(
            f"File: {result.metadata['file_path']}\n{result.text}" for result in results
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
