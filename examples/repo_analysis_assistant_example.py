"""Repository Analysis Assistant Example.

This example demonstrates a comprehensive repository analysis system that:
1. Clones and analyzes GitHub repositories
2. Uses RAG to maintain context about the codebase
3. Employs multiple specialized agents for different aspects of analysis
4. Provides interactive Q&A about the repository
5. Generates quality and architecture reports
"""

import asyncio
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, cast
import ast
import re

from git import Repo
from dotenv import load_dotenv
import radon.metrics
import radon.complexity
import radon.raw
from lizard import analyze_file

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.agents.provider import Message
from pepperpy.rag.providers.supabase import SupabaseRAGProvider
from pepperpy.rag import Document


@dataclass
class RepoAnalysis:
    """Analysis results for a repository."""
    
    # Basic info
    repo_url: str
    analysis_date: datetime
    
    # Structure analysis
    file_count: int
    directory_structure: Dict[str, Any]
    main_languages: List[str]
    
    # Quality metrics
    code_quality_score: float
    test_coverage: Optional[float]
    documentation_score: float
    
    # Architecture
    design_patterns: List[str]
    architectural_style: str
    key_components: List[str]
    
    # Dependencies
    external_dependencies: List[str]
    internal_dependencies: Dict[str, List[str]]


class RepositoryAnalysisAssistant:
    """Assistant for analyzing GitHub repositories."""

    def __init__(self) -> None:
        """Initialize the assistant."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
            
        self.rag_provider = SupabaseRAGProvider(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
        )
        self.repo_path: Optional[str] = None
        self.group_id: str = ""  # Will be set in initialize()
        self.analysis: Optional[RepoAnalysis] = None

    async def initialize(self) -> None:
        """Initialize the assistant and its components."""
        await self.rag_provider.initialize()
        
        # Define analysis tools
        tools = [
            {
                "name": "analyze_file",
                "description": "Analyze a specific file in the repository",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to analyze",
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "search_codebase",
                "description": "Search for patterns or components in the codebase",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_dependencies",
                "description": "Get project dependencies and their relationships",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {
                            "type": "string",
                            "description": "Scope of dependencies to analyze (all, direct, dev)",
                        },
                    },
                    "required": ["scope"],
                },
            },
        ]

        # Configure LLM
        llm_config = {
            "config_list": [{
                "model": "anthropic/claude-3-opus-20240229",
                "api_key": os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY", ""),
                "base_url": "https://openrouter.ai/api/v1",
                "api_type": "openai",
            }],
            "temperature": 0.7,
            "functions": tools,
        }

        # Create agent group
        self.group_id = await create_agent_group(
            agents=[
                {
                    "type": "user",
                    "name": "user",
                    "system_message": "",
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "architect",
                    "system_message": (
                        "You are a software architect specialized in:\n"
                        "1. Analyzing system architecture and design patterns\n"
                        "2. Evaluating component relationships and dependencies\n"
                        "3. Identifying architectural strengths and weaknesses\n"
                        "4. Suggesting architectural improvements\n"
                    ),
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "code_analyst",
                    "system_message": (
                        "You are a code quality analyst specialized in:\n"
                        "1. Code quality assessment\n"
                        "2. Best practices evaluation\n"
                        "3. Performance analysis\n"
                        "4. Security review\n"
                    ),
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "documentation_expert",
                    "system_message": (
                        "You are a documentation specialist focused on:\n"
                        "1. Documentation completeness and quality\n"
                        "2. API documentation review\n"
                        "3. Code comments analysis\n"
                        "4. Usage examples and tutorials\n"
                    ),
                    "config": {},
                },
            ],
            name="Repository Analysis Team",
            description="A team of experts that analyze software repositories",
            use_group_chat=True,
            llm_config=llm_config,
        )

    async def analyze_repository(self, repo_url: str) -> RepoAnalysis:
        """Analyze a GitHub repository.
        
        Args:
            repo_url: URL of the GitHub repository to analyze
            
        Returns:
            Detailed analysis of the repository
        """
        print(f"\nAnalyzing repository: {repo_url}")
        
        # Clone repository
        with tempfile.TemporaryDirectory() as temp_dir:
            print("\nCloning repository...")
            repo = Repo.clone_from(repo_url, temp_dir)
            self.repo_path = temp_dir
            
            # Index repository contents in RAG
            print("\nIndexing repository contents...")
            await self._index_repository(repo)
            
            # Analyze repository structure
            print("\nAnalyzing repository structure...")
            structure_analysis = await self._analyze_structure()
            
            # Analyze code quality
            print("\nAnalyzing code quality...")
            quality_analysis = await self._analyze_quality()
            
            # Analyze architecture
            print("\nAnalyzing architecture...")
            architecture_analysis = await self._analyze_architecture()
            
            # Create final analysis
            self.analysis = RepoAnalysis(
                repo_url=repo_url,
                analysis_date=datetime.now(),
                **structure_analysis,
                **quality_analysis,
                **architecture_analysis,
            )
            
            return self.analysis

    async def ask_question(self, question: str) -> str:
        """Ask a question about the analyzed repository.
        
        Args:
            question: Question about the repository
            
        Returns:
            Answer from the analysis team
            
        Raises:
            ValueError: If no repository has been analyzed yet
        """
        if not self.analysis:
            raise ValueError("No repository has been analyzed yet")
            
        messages = await execute_task(
            group_id=self.group_id,  # Now guaranteed to be str
            task=f"Question about the repository: {question}",
        )
        
        # Combine all messages into a single response
        response = "\n".join(msg.content for msg in messages)
        return response

    async def generate_report(self, report_type: str = "full") -> str:
        """Generate a report about the analyzed repository.
        
        Args:
            report_type: Type of report to generate (full, quality, architecture)
            
        Returns:
            Generated report
            
        Raises:
            ValueError: If no repository has been analyzed yet
        """
        if not self.analysis:
            raise ValueError("No repository has been analyzed yet")
            
        messages = await execute_task(
            group_id=self.group_id,  # Now guaranteed to be str
            task=f"Generate a {report_type} report for the analyzed repository",
        )
        
        # Combine all messages into a single report
        report = "\n".join(msg.content for msg in messages)
        return report

    async def _index_repository(self, repo: Repo) -> None:
        """Index repository contents in the RAG system."""
        if not self.repo_path:
            raise ValueError("Repository path not set")
            
        documents = []
        repo_path = Path(self.repo_path)
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    doc = Document(
                        id=file_path,
                        content=content,
                        metadata={
                            "type": "source_code",
                            "language": file.split('.')[-1],
                            "path": os.path.relpath(file_path, self.repo_path),
                        },
                    )
                    documents.append(doc)
        
        await self.rag_provider.add_documents(documents)

    async def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze repository structure."""
        if not self.repo_path:
            raise ValueError("Repository path not set")
            
        repo_path = Path(self.repo_path)
        
        # Initialize counters
        file_count = 0
        language_counter = Counter()
        directory_structure = defaultdict(list)
        
        # Analyze files
        for root, dirs, files in os.walk(repo_path):
            rel_path = os.path.relpath(root, repo_path)
            if rel_path == ".":
                rel_path = ""
                
            # Skip common directories to ignore
            if any(d.startswith('.') for d in root.split(os.sep)):
                continue
                
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                extension = os.path.splitext(file)[1].lower()
                
                # Count files by type
                file_count += 1
                if extension:
                    language_counter[extension[1:]] += 1
                    
                # Build directory structure
                directory_structure[rel_path].append({
                    "name": file,
                    "type": "file",
                    "size": os.path.getsize(file_path),
                    "language": extension[1:] if extension else "unknown"
                })
                
            # Add directories to structure
            for dir_name in dirs:
                if not dir_name.startswith('.'):
                    directory_structure[rel_path].append({
                        "name": dir_name,
                        "type": "directory"
                    })
        
        # Map common extensions to languages
        language_mapping = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'java': 'Java',
            'go': 'Go',
            'rs': 'Rust',
            'cpp': 'C++',
            'c': 'C',
            'h': 'C/C++ Header',
            'rb': 'Ruby',
            'php': 'PHP',
            'cs': 'C#',
            'scala': 'Scala',
            'kt': 'Kotlin',
            'swift': 'Swift',
        }
        
        # Convert extensions to language names
        main_languages = []
        for ext, count in language_counter.most_common(5):
            lang = language_mapping.get(ext, ext.upper())
            if count > 0:  # Only include languages that actually appear
                main_languages.append(lang)
        
        return {
            "file_count": file_count,
            "directory_structure": dict(directory_structure),
            "main_languages": main_languages,
        }

    async def _analyze_quality(self) -> Dict[str, Any]:
        """Analyze code quality."""
        if not self.repo_path:
            raise ValueError("Repository path not set")
            
        repo_path = Path(self.repo_path)
        
        # Initialize metrics
        total_files = 0
        total_lines = 0
        total_complexity = 0
        total_maintainability = 0
        test_files = 0
        documented_files = 0
        
        # Analyze each Python file (as an example, extend for other languages)
        for root, _, files in os.walk(repo_path):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Count files
                    total_files += 1
                    
                    # Basic metrics
                    metrics = radon.metrics.mi_visit(content, multi=True)
                    raw_metrics = radon.raw.analyze(content)
                    total_lines += raw_metrics.loc
                    
                    # Complexity
                    complexity = radon.complexity.cc_visit(content)
                    avg_complexity = sum(item.complexity for item in complexity) / len(complexity) if complexity else 0
                    total_complexity += avg_complexity
                    
                    # Maintainability
                    maintainability = metrics[0] if metrics else 0
                    total_maintainability += maintainability
                    
                    # Test coverage estimation (based on presence of test files and assertions)
                    if 'test' in file.lower():
                        test_files += 1
                        
                    # Documentation score (check for docstrings and comments)
                    tree = ast.parse(content)
                    has_module_docstring = (
                        isinstance(tree.body[0], ast.Expr) and 
                        isinstance(tree.body[0].value, ast.Str)
                    ) if tree.body else False
                    
                    class DocVisitor(ast.NodeVisitor):
                        def __init__(self):
                            self.has_docs = False
                            
                        def visit_FunctionDef(self, node):
                            if ast.get_docstring(node):
                                self.has_docs = True
                            self.generic_visit(node)
                            
                        def visit_ClassDef(self, node):
                            if ast.get_docstring(node):
                                self.has_docs = True
                            self.generic_visit(node)
                    
                    doc_visitor = DocVisitor()
                    doc_visitor.visit(tree)
                    
                    if has_module_docstring or doc_visitor.has_docs:
                        documented_files += 1
                        
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
        
        if total_files == 0:
            return {
                "code_quality_score": 0.0,
                "test_coverage": 0.0,
                "documentation_score": 0.0
            }
        
        # Calculate final scores
        avg_maintainability = total_maintainability / total_files
        avg_complexity = total_complexity / total_files
        
        # Normalize scores to 0-1 range
        quality_score = min(1.0, max(0.0, avg_maintainability / 100))
        test_coverage = min(1.0, max(0.0, test_files / total_files))
        documentation_score = min(1.0, max(0.0, documented_files / total_files))
        
        return {
            "code_quality_score": quality_score,
            "test_coverage": test_coverage,
            "documentation_score": documentation_score
        }

    async def _analyze_architecture(self) -> Dict[str, Any]:
        """Analyze repository architecture."""
        if not self.repo_path:
            raise ValueError("Repository path not set")
            
        repo_path = Path(self.repo_path)
        
        # Initialize analysis results
        design_patterns: Set[str] = set()
        components: Set[str] = set()
        dependencies: Dict[str, List[str]] = defaultdict(list)
        internal_deps: Dict[str, List[str]] = defaultdict(list)
        
        # Common design pattern indicators
        pattern_indicators = {
            'Factory': r'(?i)factory|create|build|make',
            'Singleton': r'(?i)instance|getInstance|shared',
            'Observer': r'(?i)observer|listener|subscribe|notify',
            'Strategy': r'(?i)strategy|algorithm|policy',
            'Adapter': r'(?i)adapter|wrapper|convert',
            'Command': r'(?i)command|execute|invoke',
            'Repository': r'(?i)repository|dao|store',
            'Service': r'(?i)service|provider|manager',
        }
        
        # Analyze Python files
        for root, _, files in os.walk(repo_path):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse imports and dependencies
                    tree = ast.parse(content)
                    
                    class DependencyVisitor(ast.NodeVisitor):
                        def __init__(self):
                            self.imports = []
                            self.internal_imports = []
                            
                        def visit_Import(self, node):
                            for name in node.names:
                                self.imports.append(name.name)
                                
                        def visit_ImportFrom(self, node):
                            if node.module:
                                if not node.module.startswith('.'):
                                    self.imports.append(node.module)
                                else:
                                    self.internal_imports.append(node.module)
                    
                    visitor = DependencyVisitor()
                    visitor.visit(tree)
                    
                    # Record dependencies
                    dependencies[rel_path].extend(visitor.imports)
                    internal_deps[rel_path].extend(visitor.internal_imports)
                    
                    # Detect design patterns
                    for pattern, pattern_regex in pattern_indicators.items():
                        if re.search(pattern_regex, content):
                            design_patterns.add(pattern)
                    
                    # Identify components from class names and module structure
                    class ComponentVisitor(ast.NodeVisitor):
                        def visit_ClassDef(self, node):
                            components.add(node.name)
                            self.generic_visit(node)
                    
                    comp_visitor = ComponentVisitor()
                    comp_visitor.visit(tree)
                    
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
        
        # Determine architectural style
        architectural_style = "Monolithic"  # Default
        if any('api' in comp.lower() for comp in components):
            if any('worker' in comp.lower() for comp in components):
                architectural_style = "Microservices"
            else:
                architectural_style = "REST API"
        elif any('plugin' in comp.lower() for comp in components):
            architectural_style = "Plugin-based"
        elif len(internal_deps) > 20:  # Arbitrary threshold
            architectural_style = "Modular Monolith"
        
        # Get key components (most referenced classes/modules)
        component_refs = Counter()
        for deps in internal_deps.values():
            component_refs.update(deps)
        
        key_components = [comp for comp, _ in component_refs.most_common(5)]
        
        return {
            "design_patterns": list(design_patterns),
            "architectural_style": architectural_style,
            "key_components": key_components,
            "external_dependencies": list(set(sum(dependencies.values(), []))),
            "internal_dependencies": dict(internal_deps)
        }

    async def shutdown(self) -> None:
        """Clean up resources."""
        if self.group_id:
            await cleanup_group(self.group_id)
        await self.rag_provider.shutdown()


async def main() -> None:
    """Run the repository analysis example."""
    # Load environment variables
    load_dotenv()
    
    # Create and initialize assistant
    assistant = RepositoryAnalysisAssistant()
    await assistant.initialize()
    
    try:
        # Example repository to analyze
        repo_url = "https://github.com/openai/whisper"
        
        # Analyze repository
        analysis = await assistant.analyze_repository(repo_url)
        
        # Print basic analysis results
        print("\nAnalysis Results:")
        print(f"Repository: {analysis.repo_url}")
        print(f"Analysis Date: {analysis.analysis_date}")
        print(f"Main Languages: {', '.join(analysis.main_languages)}")
        print(f"Code Quality Score: {analysis.code_quality_score:.2f}")
        print(f"Documentation Score: {analysis.documentation_score:.2f}")
        print(f"Architectural Style: {analysis.architectural_style}")
        
        # Ask some questions about the repository
        questions = [
            "What are the main components of this system?",
            "How is the code quality in terms of testing and documentation?",
            "What architectural patterns are used and are they appropriate?",
        ]
        
        print("\nAsking questions about the repository:")
        for question in questions:
            print(f"\nQ: {question}")
            answer = await assistant.ask_question(question)
            print(f"A: {answer}")
        
        # Generate a full report
        print("\nGenerating full analysis report...")
        report = await assistant.generate_report("full")
        print(report)
    
    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 