"""Code transformation tools for the refactoring system."""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import black
import isort

from .context import RefactoringContext

logger = logging.getLogger(__name__)


@dataclass
class ImportStatement:
    """Represents a Python import statement."""

    module: str
    names: List[str]
    alias: Optional[str] = None
    is_from: bool = False
    level: int = 0  # For relative imports


class ImportOrganizer:
    """Organize and clean up imports."""

    def __init__(self, context: RefactoringContext):
        self.context = context

    def organize_imports(self, content: str) -> str:
        """Sort and deduplicate imports.

        Args:
            content: Source code to organize

        Returns:
            Organized source code
        """
        try:
            tree = ast.parse(content)
            imports = self._collect_imports(tree)
            organized = self._sort_imports(imports)
            return self._generate_import_block(organized, content)
        except Exception as e:
            self.context.logger.error(f"Failed to organize imports: {e}")
            return content

    def _collect_imports(self, tree: ast.AST) -> List[ImportStatement]:
        """Collect all imports from AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(
                        ImportStatement(
                            module=name.name,
                            names=[name.name],
                            alias=name.asname,
                            is_from=False,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(
                    ImportStatement(
                        module=module,
                        names=[n.name for n in node.names],
                        level=node.level,
                        is_from=True,
                    )
                )

        return imports

    def _sort_imports(
        self, imports: List[ImportStatement]
    ) -> Dict[str, List[ImportStatement]]:
        """Sort imports into categories."""
        categories = {
            "future": [],  # __future__ imports
            "stdlib": [],  # Standard library
            "third_party": [],  # Third-party packages
            "local": [],  # Local imports
            "relative": [],  # Relative imports
        }

        stdlib_modules = self._get_stdlib_modules()

        for imp in imports:
            if imp.level > 0:
                categories["relative"].append(imp)
            else:
                root_pkg = imp.module.split(".")[0]
                if root_pkg == "__future__":
                    categories["future"].append(imp)
                elif root_pkg in stdlib_modules:
                    categories["stdlib"].append(imp)
                elif root_pkg.startswith("."):
                    categories["relative"].append(imp)
                elif self._is_local_import(root_pkg):
                    categories["local"].append(imp)
                else:
                    categories["third_party"].append(imp)

        # Sort within each category
        for category in categories.values():
            category.sort(key=lambda x: (x.module, x.names[0] if x.names else ""))

        return categories

    def _generate_import_block(
        self, categories: Dict[str, List[ImportStatement]], original_content: str
    ) -> str:
        """Generate organized import block."""
        import_lines = []

        # Add each category with proper spacing
        for category in ["future", "stdlib", "third_party", "local", "relative"]:
            if categories[category]:
                for imp in categories[category]:
                    if imp.is_from:
                        level = "." * imp.level
                        names = ", ".join(sorted(imp.names))
                        import_lines.append(f"from {level}{imp.module} import {names}")
                    else:
                        module = imp.module
                        if imp.alias:
                            module += f" as {imp.alias}"
                        import_lines.append(f"import {module}")
                import_lines.append("")  # Add blank line between categories

        # Find the first non-import statement
        tree = ast.parse(original_content)
        first_non_import = float("inf")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                if hasattr(node, "lineno"):
                    first_non_import = min(first_non_import, node.lineno)

        # Split content and combine
        content_lines = original_content.splitlines()
        if first_non_import < float("inf"):
            return "\n".join(import_lines + content_lines[first_non_import - 1 :])
        return "\n".join(import_lines + content_lines)

    def _get_stdlib_modules(self) -> Set[str]:
        """Get set of standard library module names."""
        import sysconfig

        stdlib_paths = [
            sysconfig.get_path("stdlib"),
            sysconfig.get_path("platstdlib"),
        ]

        stdlib_modules = set()
        for path in stdlib_paths:
            if path:
                path = Path(path)
                stdlib_modules.update(
                    f.stem for f in path.glob("*.py") if not f.stem.startswith("_")
                )

        return stdlib_modules

    def _is_local_import(self, module_name: str) -> bool:
        """Check if import is local to the project."""
        workspace_root = Path(self.context.workspace_root)
        return any(
            (workspace_root / path).exists()
            for path in [f"{module_name}.py", f"{module_name}/__init__.py"]
        )


class CodeFormatter:
    """Format code according to project standards."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self.line_length = 88  # Black's default
        self.indent = 4

    def format_code(self, content: str) -> str:
        """Format code using black and isort.

        Args:
            content: Source code to format

        Returns:
            Formatted source code
        """
        try:
            # First organize imports
            content = self._format_imports(content)

            # Then format with black
            content = self._format_with_black(content)

            return content
        except Exception as e:
            self.context.logger.error(f"Failed to format code: {e}")
            return content

    def _format_imports(self, content: str) -> str:
        """Format imports using isort."""
        try:
            config = isort.Config(
                line_length=self.line_length,
                multi_line_output=3,  # Vertical hanging indent
                include_trailing_comma=True,
                force_grid_wrap=0,
                use_parentheses=True,
                ensure_newline_before_comments=True,
                indent=self.indent,
            )
            return isort.code(content, config=config)
        except Exception as e:
            self.context.logger.warning(f"Failed to format imports: {e}")
            return content

    def _format_with_black(self, content: str) -> str:
        """Format code using black."""
        try:
            mode = black.FileMode(
                line_length=self.line_length, string_normalization=True, is_pyi=False
            )
            return black.format_str(content, mode=mode)
        except Exception as e:
            self.context.logger.warning(f"Failed to format with black: {e}")
            return content


class DeadCodeEliminator:
    """Find and remove unused code."""

    def __init__(self, context: RefactoringContext):
        self.context = context

    def find_dead_code(
        self, tree: ast.AST
    ) -> Tuple[List[ast.AST], List[ast.AST], List[ast.AST]]:
        """Identify unused functions, classes, and imports.

        Args:
            tree: AST to analyze

        Returns:
            Tuple of (unused_imports, unused_functions, unused_classes)
        """
        try:
            return (
                self._find_unused_imports(tree),
                self._find_unused_functions(tree),
                self._find_unused_classes(tree),
            )
        except Exception as e:
            self.context.logger.error(f"Failed to find dead code: {e}")
            return [], [], []

    def _find_unused_imports(self, tree: ast.AST) -> List[ast.AST]:
        """Find unused imports."""

        class ImportVisitor(ast.NodeVisitor):
            def __init__(self):
                self.imported = {}  # name -> node
                self.used = set()

            def visit_Import(self, node):
                for name in node.names:
                    self.imported[name.asname or name.name] = node

            def visit_ImportFrom(self, node):
                for name in node.names:
                    if name.name != "*":
                        self.imported[name.asname or name.name] = node

            def visit_Name(self, node):
                self.used.add(node.id)

        visitor = ImportVisitor()
        visitor.visit(tree)

        return [
            node for name, node in visitor.imported.items() if name not in visitor.used
        ]

    def _find_unused_functions(self, tree: ast.AST) -> List[ast.AST]:
        """Find unused functions."""

        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.defined = {}  # name -> node
                self.used = set()

            def visit_FunctionDef(self, node):
                self.defined[node.name] = node
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    self.used.add(node.id)

        visitor = FunctionVisitor()
        visitor.visit(tree)

        return [
            node
            for name, node in visitor.defined.items()
            if name not in visitor.used and not name.startswith("_")
        ]

    def _find_unused_classes(self, tree: ast.AST) -> List[ast.AST]:
        """Find unused classes."""

        class ClassVisitor(ast.NodeVisitor):
            def __init__(self):
                self.defined = {}  # name -> node
                self.used = set()

            def visit_ClassDef(self, node):
                self.defined[node.name] = node
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    self.used.add(node.id)

        visitor = ClassVisitor()
        visitor.visit(tree)

        return [
            node
            for name, node in visitor.defined.items()
            if name not in visitor.used and not name.startswith("_")
        ]

    def remove_dead_code(self, content: str) -> str:
        """Remove dead code from source.

        Args:
            content: Source code to clean

        Returns:
            Cleaned source code
        """
        try:
            tree = ast.parse(content)
            unused_imports, unused_funcs, unused_classes = self.find_dead_code(tree)

            # Remove unused nodes
            class RemoveVisitor(ast.NodeTransformer):
                def visit_Import(self, node):
                    if node in unused_imports:
                        return None
                    return node

                def visit_ImportFrom(self, node):
                    if node in unused_imports:
                        return None
                    return node

                def visit_FunctionDef(self, node):
                    if node in unused_funcs:
                        return None
                    return node

                def visit_ClassDef(self, node):
                    if node in unused_classes:
                        return None
                    return node

            cleaned = RemoveVisitor().visit(tree)
            return ast.unparse(cleaned)
        except Exception as e:
            self.context.logger.error(f"Failed to remove dead code: {e}")
            return content
