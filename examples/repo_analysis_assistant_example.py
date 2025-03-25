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
from typing import Optional

from pepperpy.tools.repository import RepositoryAnalyzer
from pepperpy.tools.repository.providers import GitHubProvider
from pepperpy.rag import (
    Document, 
    Query, 
    RAGContext, 
    ChromaProvider
)
from pepperpy.llm.base import Message, MessageRole
from pepperpy.core import ValidationError, Config
from pepperpy.llm.providers import OpenRouterProvider


async def analyze_repository(repo_identifier):
    """Analyze a repository and generate a report."""
    # Initialize GitHub provider (token is automatically loaded from environment)
    github = GitHubProvider()
    
    # Create repository analyzer with GitHub provider
    # Output directory is automatically created by the library
    analyzer = RepositoryAnalyzer(
        provider=github,
        output_dir="examples/output/repo_analysis"
    )
    
    print(f"\nAnalyzing GitHub repository: {repo_identifier}")
    
    # Run analysis pipeline
    report = await analyzer.analyze(repo_identifier)
    
    # Save the analysis report
    report_path = analyzer.save_report(report)
    
    return report, report_path, github


async def index_repository(github, repo_identifier):
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
                        content=content,
                        metadata={
                            "file_path": file["path"],
                            "file_name": file["name"],
                            "repo": repo_identifier
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    print(f"Error indexing file {file['path']}: {e}")
        
        # Initialize RAG provider
        rag_provider = ChromaProvider(collection_name=f"repo-{repo_identifier.replace('/', '-')}")
        rag_context = RAGContext(provider=rag_provider)
        
        # Add documents to RAG provider
        await rag_provider.add_documents(documents)
        print(f"Indexed {len(documents)} files from repository")
        
        return rag_context
        
    except Exception as e:
        print(f"Error indexing repository: {e}")
        return None


async def ask_about_repository(question: str, report, rag_context):
    """Ask a question about the repository."""
    # First, retrieve relevant documents
    results = await rag_context.provider.search(question, top_k=5)
    
    # Build context from analysis report and retrieved documents
    context = _build_context_from_report(report)
    
    # Add retrieved documents to context
    for result in results:
        context += f"\nFile: {result.document.metadata.get('file_path')}\n"
        content = result.document.content[:1000]
        context += f"Content: {content}...\n"
    
    # Get API key from environment
    api_key = os.getenv("PEPPERPY_LLM__API_KEY")
    if not api_key:
        raise ValidationError("PEPPERPY_LLM__API_KEY environment variable not set")
    
    # Initialize LLM from environment configuration
    llm = OpenRouterProvider(
        api_key=os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY"),
        model="anthropic/claude-3-sonnet"
    )
    await llm.initialize()
    
    try:
        # Generate response
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are an expert repository analyst. Help answer questions about the repository."),
            Message(role=MessageRole.USER, content=f"""
Repository: {report.repository_name}
Analysis:
{context}

Question: {question}

Please answer the question based on the repository information and analysis.""")
        ]
        
        result = await llm.generate(messages)
        return result.content
    finally:
        await llm.cleanup()


def _build_context_from_report(report):
    """Build context from analysis report."""
    context = f"Repository: {report.repository_name} ({report.repository_url})\n"
    context += f"Files: {report.structure.files_count}\n"
    context += f"Languages: {', '.join(f'{lang} ({pct:.1f}%)' for lang, pct in report.structure.languages.items())}\n"
    context += f"Code Quality: Maintainability {report.code_quality.maintainability_index:.1f}/100, "
    context += f"Test Coverage {report.code_quality.test_coverage:.1f}%, "
    context += f"Doc Coverage {report.code_quality.documentation_coverage:.1f}%\n"
    
    # Add issues
    total_issues = sum(len(issues) for issues in report.code_quality.issues.values())
    context += f"Issues Found: {total_issues}\n"
    for severity, issues in report.code_quality.issues.items():
        if issues:
            context += f"- {severity.capitalize()}: {len(issues)} issues\n"
            for issue in issues:
                context += f"  - {issue['file']}:{issue['line']} - {issue['message']}\n"
    
    # Add recommendations
    context += "Recommendations:\n"
    for i, rec in enumerate(report.recommendations, 1):
        context += f"{i}. {rec}\n"
        
    return context


def _is_text_file(filename: str) -> bool:
    """Check if a file is a text file based on extension."""
    text_extensions = [
        '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json', '.md',
        '.txt', '.yml', '.yaml', '.toml', '.rst', '.go', '.c', '.cpp', '.h',
        '.java', '.rb', '.sh', '.bash', '.php', '.rs', '.lua'
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
            model="anthropic/claude-3-sonnet"
        )
        
        # Initialize RAG provider
        self.rag = ChromaProvider(collection_name="repo_analysis", persist_directory=".pepperpy/chroma")

    async def analyze(self) -> None:
        """Analyze the repository and index its content."""
        # Initialize providers
        await self.llm.initialize()
        await self.rag.initialize()
        
        # Analyze repository
        report, report_path, github = await analyze_repository(self.repo_url)
        
        # Display summary information
        print(f"\nRepository Analysis Summary:")
        print(f"Repository: {report.repository_name} ({report.repository_url})")
        print(f"Files: {report.structure.files_count}")
        print(f"Languages: {', '.join(f'{lang} ({pct:.1f}%)' for lang, pct in report.structure.languages.items())}")
        print(f"Code Quality:")
        print(f"  - Maintainability: {report.code_quality.maintainability_index:.1f}/100")
        print(f"  - Test Coverage: {report.code_quality.test_coverage:.1f}%")
        print(f"  - Doc Coverage: {report.code_quality.documentation_coverage:.1f}%")
        
        # Display issues summary
        total_issues = sum(len(issues) for issues in report.code_quality.issues.values())
        print(f"Issues Found: {total_issues}")
        for severity, issues in report.code_quality.issues.items():
            if issues:
                print(f"  - {severity.capitalize()}: {len(issues)}")
        
        # Display top recommendations
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"{i}. {rec}")
        
        print(f"\nFull report saved to: {report_path}")
        
        # Index repository for RAG
        rag_context = await index_repository(github, self.repo_url)
        if not rag_context:
            print("Error indexing repository, cannot answer questions")
            return
        
        # Example questions about the repository
        questions = [
            "What is the main purpose of this repository?",
            "What are the main components of the architecture?",
            "What are the most critical issues that need to be fixed?",
            "How is the code quality overall?",
            "What improvements would you suggest for the test coverage?"
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
        results = await self.rag.search(question)
        
        # Build context from documents
        context_text = "\n\n".join(result.document.content for result in results)
            
        # Generate response using LLM
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful repository analysis assistant."),
            Message(role=MessageRole.USER, content=f"Question about the repository: {question}\n\nContext: {context_text}")
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