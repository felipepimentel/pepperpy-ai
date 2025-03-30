"""AI-assisted code search and pattern matching utilities."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .context import RefactoringContext


@dataclass
class CodeMatch:
    """Represents a matched code block."""

    file_path: str
    start_line: int
    end_line: int
    code_block: str
    similarity_score: float
    context: Optional[str] = None


class AICodeSearcher:
    """Intelligent code search and pattern matching."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self._cache: Dict[str, List[CodeMatch]] = {}

    def find_similar_implementations(self, pattern: str) -> List[CodeMatch]:
        """Find implementations similar to the given pattern.

        Args:
            pattern: Code pattern or semantic description to search for

        Returns:
            List of matching code blocks with similarity scores
        """
        # Check cache first
        if pattern in self._cache:
            return self._cache[pattern]

        matches = []
        python_files = Path(self.context.workspace_root).rglob("*.py")

        for file_path in python_files:
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                # Parse the file
                tree = ast.parse(content)

                # Find class and function definitions
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        # Get the code block
                        code_block = ast.get_source_segment(content, node)
                        if not code_block:
                            continue

                        # Calculate similarity score
                        score = self._calculate_similarity(code_block, pattern)

                        if score > 0.7:  # Threshold for similarity
                            matches.append(
                                CodeMatch(
                                    file_path=str(file_path),
                                    start_line=getattr(node, "lineno", 0),
                                    end_line=getattr(
                                        node, "end_lineno", getattr(node, "lineno", 0)
                                    ),
                                    code_block=code_block,
                                    similarity_score=score,
                                    context=self._get_context(content, node),
                                )
                            )

            except Exception as e:
                self.context.logger.warning(f"Error processing {file_path}: {e}")
                continue

        # Sort by similarity score
        matches.sort(key=lambda x: x.similarity_score, reverse=True)

        # Cache the results
        self._cache[pattern] = matches

        return matches

    def find_pattern_usage(self, pattern: str) -> List[CodeMatch]:
        """Find where a specific pattern is used in the codebase.

        Args:
            pattern: Code pattern to search for

        Returns:
            List of code blocks where the pattern is used
        """
        matches = []
        python_files = Path(self.context.workspace_root).rglob("*.py")

        for file_path in python_files:
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                # Find direct usage
                if pattern in content:
                    # Parse to get proper context
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.AST):
                            code_block = ast.get_source_segment(content, node)
                            if code_block and pattern in code_block:
                                matches.append(
                                    CodeMatch(
                                        file_path=str(file_path),
                                        start_line=getattr(node, "lineno", 0),
                                        end_line=getattr(
                                            node,
                                            "end_lineno",
                                            getattr(node, "lineno", 0),
                                        ),
                                        code_block=code_block,
                                        similarity_score=1.0
                                        if pattern == code_block
                                        else 0.9,
                                        context=self._get_context(content, node),
                                    )
                                )

            except Exception as e:
                self.context.logger.warning(f"Error processing {file_path}: {e}")
                continue

        return matches

    def _calculate_similarity(self, code_block: str, pattern: str) -> float:
        """Calculate similarity between code block and pattern.

        This is a simple implementation that could be enhanced with:
        - AST-based comparison
        - Semantic similarity using embeddings
        - Token-based similarity
        """
        # Convert both to sets of lines for comparison
        code_lines = set(code_block.split("\n"))
        pattern_lines = set(pattern.split("\n"))

        # Calculate Jaccard similarity
        intersection = len(code_lines.intersection(pattern_lines))
        union = len(code_lines.union(pattern_lines))

        return intersection / union if union > 0 else 0.0

    def _get_context(self, content: str, node: ast.AST) -> str:
        """Get the surrounding context of a code block."""
        lines = content.split("\n")

        # Get line numbers safely
        lineno = getattr(node, "lineno", 0)
        end_lineno = getattr(node, "end_lineno", lineno)

        # Get 3 lines before and after
        start = max(0, lineno - 4)
        end = min(len(lines), end_lineno + 3)

        return "\n".join(lines[start:end])
