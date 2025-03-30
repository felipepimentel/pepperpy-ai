"""Code pattern analysis and suggestion utilities."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from .context import RefactoringContext


@dataclass
class MethodPattern:
    """Represents a method implementation pattern."""

    name: str
    args: List[str]
    return_type: Optional[str]
    decorators: List[str]
    is_async: bool
    docstring: Optional[str]
    body_pattern: str


@dataclass
class ClassPattern:
    """Represents a class implementation pattern."""

    name: str
    bases: List[str]
    methods: List[MethodPattern]
    class_vars: List[str]
    decorators: List[str]
    docstring: Optional[str]


@dataclass
class ModulePattern:
    """Represents a module's implementation pattern."""

    imports: List[str]
    classes: List[ClassPattern]
    functions: List[MethodPattern]
    constants: List[str]
    docstring: Optional[str]


class CodePatternAnalyzer:
    """Analyzes and extracts code patterns from the codebase."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self._pattern_cache: Dict[str, ModulePattern] = {}

    def extract_module_pattern(self, module_path: str) -> ModulePattern:
        """Extract implementation patterns from a module.

        Args:
            module_path: Path to the module to analyze

        Returns:
            ModulePattern containing the extracted patterns
        """
        # Check cache
        if module_path in self._pattern_cache:
            return self._pattern_cache[module_path]

        try:
            with open(module_path, "r") as f:
                content = f.read()

            # Parse the module
            tree = ast.parse(content)

            # Extract patterns
            pattern = ModulePattern(
                imports=self._extract_imports(tree),
                classes=self._extract_classes(tree),
                functions=self._extract_functions(tree),
                constants=self._extract_constants(tree),
                docstring=ast.get_docstring(tree),
            )

            # Cache the result
            self._pattern_cache[module_path] = pattern

            return pattern

        except Exception as e:
            self.context.logger.error(f"Error analyzing {module_path}: {e}")
            raise

    def suggest_implementation(self, base_class: str) -> Dict:
        """Suggest implementation based on existing patterns.

        Args:
            base_class: Name of the base class to implement

        Returns:
            Dictionary with implementation suggestions
        """
        # Find the base class in the codebase
        base_patterns = []
        python_files = Path(self.context.workspace_root).rglob("*.py")

        for file_path in python_files:
            try:
                pattern = self.extract_module_pattern(str(file_path))

                # Look for classes that inherit from base_class
                for class_pattern in pattern.classes:
                    if base_class in class_pattern.bases:
                        base_patterns.append(class_pattern)

            except Exception:
                continue

        if not base_patterns:
            raise ValueError(f"No implementations found for {base_class}")

        # Analyze common patterns
        required_methods = self._get_required_methods(base_patterns)
        common_patterns = self._extract_common_patterns(base_patterns)

        return {
            "required_methods": required_methods,
            "common_patterns": common_patterns,
            "example_implementations": base_patterns,
        }

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(f"import {name.name}")
            elif isinstance(node, ast.ImportFrom):
                names = ", ".join(n.name for n in node.names)
                imports.append(f"from {node.module} import {names}")

        return imports

    def _extract_classes(self, tree: ast.AST) -> List[ClassPattern]:
        """Extract class patterns from AST."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract class variables first
                class_vars = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_vars.append(target.id)

                classes.append(
                    ClassPattern(
                        name=node.name,
                        bases=[self._get_base_name(base) for base in node.bases],
                        methods=self._extract_methods(node),
                        class_vars=class_vars,
                        decorators=[
                            self._get_decorator_name(d) for d in node.decorator_list
                        ],
                        docstring=ast.get_docstring(node),
                    )
                )

        return classes

    def _extract_methods(self, class_node: ast.ClassDef) -> List[MethodPattern]:
        """Extract method patterns from a class definition."""
        methods = []

        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(
                    MethodPattern(
                        name=node.name,
                        args=self._get_arg_names(node.args),
                        return_type=self._get_return_type(node),
                        decorators=[
                            self._get_decorator_name(d) for d in node.decorator_list
                        ],
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        docstring=ast.get_docstring(node),
                        body_pattern=self._extract_body_pattern(node),
                    )
                )

        return methods

    def _extract_functions(self, tree: ast.AST) -> List[MethodPattern]:
        """Extract function patterns from AST."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods inside classes
                if any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                    continue

                functions.append(
                    MethodPattern(
                        name=node.name,
                        args=self._get_arg_names(node.args),
                        return_type=self._get_return_type(node),
                        decorators=[
                            self._get_decorator_name(d) for d in node.decorator_list
                        ],
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        docstring=ast.get_docstring(node),
                        body_pattern=self._extract_body_pattern(node),
                    )
                )

        return functions

    def _extract_constants(self, tree: ast.AST) -> List[str]:
        """Extract constant definitions from AST."""
        constants = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append(target.id)

        return constants

    def _get_base_name(self, node: ast.expr) -> str:
        """Get the string representation of a base class."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        return str(node)

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get the string representation of a decorator."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        return str(node)

    def _get_arg_names(self, args: ast.arguments) -> List[str]:
        """Get argument names from an arguments node."""
        names = []

        # Add positional args
        for arg in args.posonlyargs + args.args:
            names.append(arg.arg)

        # Add varargs if present
        if args.vararg:
            names.append(f"*{args.vararg.arg}")

        # Add keyword args
        for arg in args.kwonlyargs:
            names.append(arg.arg)

        # Add kwargs if present
        if args.kwarg:
            names.append(f"**{args.kwarg.arg}")

        return names

    def _get_return_type(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Optional[str]:
        """Get return type annotation if present."""
        if node.returns:
            return ast.unparse(node.returns)
        return None

    def _extract_body_pattern(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> str:
        """Extract a pattern from the function body."""
        # Convert body list to a Module node for unparse
        module = ast.Module(body=node.body, type_ignores=[])
        return ast.unparse(module)

    def _get_required_methods(self, patterns: List[ClassPattern]) -> Set[str]:
        """Get set of methods that appear in all implementations."""
        if not patterns:
            return set()

        # Start with methods from first pattern
        required = {m.name for m in patterns[0].methods}

        # Intersect with methods from other patterns
        for pattern in patterns[1:]:
            required &= {m.name for m in pattern.methods}

        return required

    def _extract_common_patterns(self, patterns: List[ClassPattern]) -> Dict:
        """Extract common implementation patterns."""
        return {
            "common_methods": self._get_required_methods(patterns),
            "common_vars": self._get_common_vars(patterns),
            "common_decorators": self._get_common_decorators(patterns),
        }

    def _get_common_vars(self, patterns: List[ClassPattern]) -> Set[str]:
        """Get class variables that appear in all implementations."""
        if not patterns:
            return set()

        common = set(patterns[0].class_vars)
        for pattern in patterns[1:]:
            common &= set(pattern.class_vars)

        return common

    def _get_common_decorators(self, patterns: List[ClassPattern]) -> Set[str]:
        """Get decorators that appear in all implementations."""
        if not patterns:
            return set()

        common = set(patterns[0].decorators)
        for pattern in patterns[1:]:
            common &= set(pattern.decorators)

        return common
