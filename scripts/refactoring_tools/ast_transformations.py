#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AST-based code transformations.

This module provides classes for advanced source code transformations using
the Abstract Syntax Tree (AST) and other parsing tools.
"""

import ast
from pathlib import Path
from typing import Any, Union

# Make imports more robust with fallbacks
try:
    import astor
except ImportError:
    # Define a dummy astor module for minimal functionality
    class DummyAstor:
        def to_source(self, ast_node):
            return f"# Could not generate source from AST: astor module not available\n# AST: {ast_node}"

    astor = DummyAstor()
    print("Warning: astor module not available. Some functionality will be limited.")

LIBCST_AVAILABLE = False
try:
    import libcst as cst

    LIBCST_AVAILABLE = True
except ImportError:
    # Define a dummy cst module for minimal functionality
    class DummyCst:
        class CSTTransformer:
            def leave_ClassDef(self, original_node, updated_node):
                return updated_node

        class ClassDef:
            pass

        class Arg:
            pass

        class Name:
            pass

        class IndentedBlock:
            pass

        class SimpleStatementLine:
            pass

        class Expr:
            pass

        class Ellipsis:
            pass

    cst = DummyCst()
    print("Warning: libcst module not available. Some functionality will be limited.")

from .common import RefactoringContext, logger


class MethodExtractor(ast.NodeTransformer):
    """Extracts code blocks into new methods."""

    def __init__(self, start_line: int, end_line: int, new_method_name: str):
        self.start_line = start_line
        self.end_line = end_line
        self.new_method_name = new_method_name
        self.target_class = None
        self.target_function = None
        self.extracted_nodes = []
        self.parameters = []
        self.referenced_vars = set()
        self.local_vars = set()
        self.return_vars = set()
        self.has_return = False

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Process class definitions."""
        self.target_class = node
        self.generic_visit(node)

        # If the extraction was from a method in this class, add the new method
        if self.extracted_nodes:
            # Create parameter list based on referenced vars
            params = [ast.arg(arg="self", annotation=None)]
            for var in sorted(self.referenced_vars - self.local_vars):
                params.append(ast.arg(arg=var, annotation=None))

            # Create arguments node
            arguments = ast.arguments(
                posonlyargs=[],
                args=params,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None,
            )

            # Create return statement if needed
            if self.return_vars:
                return_vars = [
                    ast.Name(id=var, ctx=ast.Load()) for var in sorted(self.return_vars)
                ]
                if len(return_vars) == 1:
                    return_stmt = ast.Return(value=return_vars[0])
                else:
                    return_stmt = ast.Return(
                        value=ast.Tuple(elts=return_vars, ctx=ast.Load())
                    )

                self.extracted_nodes.append(return_stmt)

            # Create the new method
            new_method = ast.FunctionDef(
                name=self.new_method_name,
                args=arguments,
                body=self.extracted_nodes,
                decorator_list=[],
                returns=None,
            )

            # Add the new method to the class
            node.body.append(new_method)

        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Process function definitions."""
        # Check if this function contains the lines we want to extract
        start_line = getattr(node, "lineno", 0)
        end_line = start_line + len(node.body)

        if start_line <= self.start_line and end_line >= self.end_line:
            self.target_function = node

            # Collect local variables defined in this function
            for n in ast.walk(node):
                if isinstance(n, ast.Assign):
                    for target in n.targets:
                        if isinstance(target, ast.Name):
                            self.local_vars.add(target.id)

            # Extract the nodes within the specified lines
            extracted_body = []
            replacement_body = []
            within_range = False

            for stmt in node.body:
                stmt_line = getattr(stmt, "lineno", 0)

                if self.start_line <= stmt_line <= self.end_line:
                    within_range = True

                    # Collect variable references in the extracted code
                    for subnode in ast.walk(stmt):
                        if isinstance(subnode, ast.Name) and isinstance(
                            subnode.ctx, ast.Load
                        ):
                            self.referenced_vars.add(subnode.id)

                    # Save the statement for extraction
                    extracted_body.append(stmt)
                else:
                    # Check for variables that need to be returned
                    if within_range:
                        for subnode in ast.walk(stmt):
                            if (
                                isinstance(subnode, ast.Name)
                                and isinstance(subnode.ctx, ast.Load)
                                and subnode.id in self.local_vars
                                and stmt_line > self.end_line
                            ):
                                self.return_vars.add(subnode.id)

                    replacement_body.append(stmt)

            # Build the method call
            if self.target_class:
                # This is a method, so it should have self
                args = [
                    ast.Name(id=var, ctx=ast.Load())
                    for var in sorted(self.referenced_vars - self.local_vars)
                ]

                method_call = ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()),
                        attr=self.new_method_name,
                        ctx=ast.Load(),
                    ),
                    args=args,
                    keywords=[],
                )
            else:
                # This is a standalone function
                args = [
                    ast.Name(id=var, ctx=ast.Load())
                    for var in sorted(self.referenced_vars)
                ]

                method_call = ast.Call(
                    func=ast.Name(id=self.new_method_name, ctx=ast.Load()),
                    args=args,
                    keywords=[],
                )

            # Handle return value assignment
            if self.return_vars:
                if len(self.return_vars) == 1:
                    var = list(self.return_vars)[0]
                    assign_stmt = ast.Assign(
                        targets=[ast.Name(id=var, ctx=ast.Store())], value=method_call
                    )
                else:
                    targets = [
                        ast.Name(id=var, ctx=ast.Store())
                        for var in sorted(self.return_vars)
                    ]
                    assign_stmt = ast.Assign(
                        targets=[ast.Tuple(elts=targets, ctx=ast.Store())],
                        value=method_call,
                    )

                replacement_body.insert(0, assign_stmt)
            else:
                # Just call the method
                replacement_body.insert(0, ast.Expr(value=method_call))

            # Save the extracted nodes for later
            self.extracted_nodes = extracted_body

            # Replace the function body
            node.body = replacement_body

        return self.generic_visit(node)


class ProtocolTransformer(cst.CSTTransformer if LIBCST_AVAILABLE else object):
    """Converts classes to Protocol interfaces."""

    def __init__(self, class_name: str):
        super().__init__()
        self.class_name = class_name
        self.found_class = False

    def leave_ClassDef(self, original_node: Any, updated_node: Any) -> Any:
        """Process class definitions when leaving the node."""
        if not LIBCST_AVAILABLE:
            logger.error("Cannot convert to protocol: libcst module not available")
            return updated_node

        if original_node.name.value == self.class_name:
            self.found_class = True

            # Add Protocol to base classes
            bases = list(updated_node.bases)
            protocol_base = cst.Arg(value=cst.Name("Protocol"))

            if not bases:
                bases = [protocol_base]
            else:
                bases.append(protocol_base)

            # Convert methods to protocol methods (removing implementation)
            new_body = []
            for item in updated_node.body.body:
                if isinstance(item, cst.FunctionDef):
                    # Replace function body with ellipsis
                    new_body.append(
                        item.with_changes(
                            body=cst.IndentedBlock(
                                body=[
                                    cst.SimpleStatementLine(
                                        body=[cst.Expr(value=cst.Ellipsis())]
                                    )
                                ]
                            )
                        )
                    )
                else:
                    new_body.append(item)

            # Update the class
            return updated_node.with_changes(
                bases=bases, body=updated_node.body.with_changes(body=new_body)
            )

        return updated_node


class FunctionToClassTransformer(ast.NodeTransformer):
    """Converts functions to classes."""

    def __init__(self, function_name: str):
        self.function_name = function_name
        self.params = []
        self.found_function = False

    def visit_FunctionDef(
        self, node: ast.FunctionDef
    ) -> Union[ast.FunctionDef, ast.ClassDef]:
        """Process function definitions."""
        if node.name == self.function_name:
            self.found_function = True

            # Get parameter list
            self.params = [arg.arg for arg in node.args.args]

            # Create __init__ method
            init_params = [ast.arg(arg="self", annotation=None)]
            init_params.extend(node.args.args)

            init_body = []
            for param in self.params:
                init_body.append(
                    ast.Assign(
                        targets=[
                            ast.Attribute(
                                value=ast.Name(id="self", ctx=ast.Load()),
                                attr=param,
                                ctx=ast.Store(),
                            )
                        ],
                        value=ast.Name(id=param, ctx=ast.Load()),
                    )
                )

            init_method = ast.FunctionDef(
                name="__init__",
                args=ast.arguments(
                    posonlyargs=[],
                    args=init_params,
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                    vararg=None,
                    kwarg=None,
                ),
                body=init_body,
                decorator_list=[],
                returns=None,
            )

            # Create call method with the original function body
            call_body = []
            for stmt in node.body:
                # Replace parameter references with self.param
                call_body.append(self._replace_params(stmt))

            call_method = ast.FunctionDef(
                name="__call__",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="self", annotation=None)],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                    vararg=None,
                    kwarg=None,
                ),
                body=call_body,
                decorator_list=[],
                returns=node.returns,
            )

            # Create the class
            class_name = f"{self.function_name[0].upper()}{self.function_name[1:]}"
            class_def = ast.ClassDef(
                name=class_name,
                bases=[],
                keywords=[],
                body=[init_method, call_method],
                decorator_list=[],
            )

            # Add proper line number and column offset
            class_def.lineno = node.lineno
            class_def.col_offset = node.col_offset

            return class_def

        return self.generic_visit(node)

    def _replace_params(self, node: ast.AST) -> ast.AST:
        """Replace parameter references with self.param references."""

        class ParamReplacer(ast.NodeTransformer):
            def __init__(self, params):
                self.params = params

            def visit_Name(self, node: ast.Name) -> Union[ast.Name, ast.Attribute]:
                """Replace parameter references."""
                if isinstance(node.ctx, ast.Load) and node.id in self.params:
                    return ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()),
                        attr=node.id,
                        ctx=node.ctx,
                    )
                return node

        return ParamReplacer(self.params).visit(node)


def extract_method(
    file_path: str,
    start_line: int,
    end_line: int,
    new_method_name: str,
    context: RefactoringContext,
) -> None:
    """
    Extract a code block into a new method.

    Args:
        file_path: Path to the file
        start_line: Start line (1-indexed)
        end_line: End line (1-indexed)
        new_method_name: Name for the new method
        context: Refactoring context
    """
    logger.info(
        f"Extracting method {new_method_name} from lines {start_line}-{end_line} in {file_path}"
    )

    try:
        # Parse the file
        file_content = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(file_content)

        # Apply the transformation
        transformer = MethodExtractor(start_line, end_line, new_method_name)
        modified_tree = transformer.visit(tree)

        # Generate the new source code
        modified_code = astor.to_source(modified_tree)

        # Backup the original file
        if context.backup:
            backup_path = Path(file_path).with_suffix(".py.bak")
            backup_path.write_text(file_content, encoding="utf-8")
            logger.info(f"Created backup: {backup_path}")

        # Write the modified file
        if not context.dry_run:
            Path(file_path).write_text(modified_code, encoding="utf-8")
            logger.info(f"Extracted method {new_method_name} in {file_path}")
        else:
            logger.info(f"Would extract method {new_method_name} in {file_path}")

    except Exception as e:
        logger.error(f"Error extracting method: {e}")


def convert_to_protocol(
    file_path: str, class_name: str, context: RefactoringContext
) -> None:
    """
    Convert a class to a Protocol interface.

    Args:
        file_path: Path to the file
        class_name: Name of the class to convert
        context: Refactoring context
    """
    logger.info(f"Converting class {class_name} to Protocol in {file_path}")

    try:
        # Parse the file
        file_content = Path(file_path).read_text(encoding="utf-8")

        # Parse with libcst
        module = cst.parse_module(file_content)

        # Apply the transformation
        transformer = ProtocolTransformer(class_name)
        modified_module = module.visit(transformer)

        if not transformer.found_class:
            logger.warning(f"Class {class_name} not found in {file_path}")
            return

        # Add Protocol import if needed
        # This is a simplification - a proper implementation would check if it's already imported
        modified_code = "from typing import Protocol\n\n" + modified_module.code

        # Backup the original file
        if context.backup:
            backup_path = Path(file_path).with_suffix(".py.bak")
            backup_path.write_text(file_content, encoding="utf-8")
            logger.info(f"Created backup: {backup_path}")

        # Write the modified file
        if not context.dry_run:
            Path(file_path).write_text(modified_code, encoding="utf-8")
            logger.info(f"Converted class {class_name} to Protocol in {file_path}")
        else:
            logger.info(f"Would convert class {class_name} to Protocol in {file_path}")

    except Exception as e:
        logger.error(f"Error converting to Protocol: {e}")


def function_to_class(
    file_path: str, function_name: str, context: RefactoringContext
) -> None:
    """
    Convert a function to a class.

    Args:
        file_path: Path to the file
        function_name: Name of the function to convert
        context: Refactoring context
    """
    logger.info(f"Converting function {function_name} to class in {file_path}")

    try:
        # Parse the file
        file_content = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(file_content)

        # Apply the transformation
        transformer = FunctionToClassTransformer(function_name)
        modified_tree = transformer.visit(tree)

        if not transformer.found_function:
            logger.warning(f"Function {function_name} not found in {file_path}")
            return

        # Generate the new source code
        modified_code = astor.to_source(modified_tree)

        # Backup the original file
        if context.backup:
            backup_path = Path(file_path).with_suffix(".py.bak")
            backup_path.write_text(file_content, encoding="utf-8")
            logger.info(f"Created backup: {backup_path}")

        # Write the modified file
        if not context.dry_run:
            Path(file_path).write_text(modified_code, encoding="utf-8")
            logger.info(f"Converted function {function_name} to class in {file_path}")
        else:
            logger.info(
                f"Would convert function {function_name} to class in {file_path}"
            )

    except Exception as e:
        logger.error(f"Error converting function to class: {e}")


def extract_public_api(module_path: str, context: RefactoringContext) -> None:
    """
    Extract public API into __init__.py file.

    Args:
        module_path: Path to the module directory
        context: Refactoring context
    """
    logger.info(f"Extracting public API from {module_path}")

    try:
        module_dir = Path(module_path)
        init_path = module_dir / "__init__.py"

        # Collect public symbols from all Python files in the module
        public_symbols = {}

        for file_path in module_dir.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            file_content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(file_content)

            # Find all public functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # Skip private symbols (starting with _)
                    if not node.name.startswith("_"):
                        module_name = file_path.stem
                        if module_name not in public_symbols:
                            public_symbols[module_name] = []
                        public_symbols[module_name].append(node.name)

        # Create the new __init__.py content
        content = '"""Public API for the module."""\n\n'

        all_symbols = []

        for module_name, symbols in sorted(public_symbols.items()):
            if symbols:
                content += f"# From {module_name}\n"
                for symbol in sorted(symbols):
                    content += f"from .{module_name} import {symbol}\n"
                    all_symbols.append(symbol)
                content += "\n"

        content += f"__all__ = {all_symbols!r}\n"

        # Backup the original file
        if context.backup and init_path.exists():
            backup_path = init_path.with_suffix(".py.bak")
            backup_path.write_text(
                init_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            logger.info(f"Created backup: {backup_path}")

        # Write the new __init__.py
        if not context.dry_run:
            init_path.write_text(content, encoding="utf-8")
            logger.info(f"Extracted public API to {init_path}")
        else:
            logger.info(f"Would extract public API to {init_path}")

    except Exception as e:
        logger.error(f"Error extracting public API: {e}")


def generate_factory(
    class_name: str, output_file: str, context: RefactoringContext
) -> None:
    """
    Generate a Factory pattern implementation.

    Args:
        class_name: Name of the class for which to generate the factory
        output_file: Path to the output file
        context: Refactoring context
    """
    logger.info(f"Generating factory for {class_name} in {output_file}")

    try:
        factory_code = f'''"""Factory for {class_name} instances."""

from typing import Dict, Type, Any


class {class_name}Factory:
    """Factory for creating {class_name} instances."""
    
    _registry: Dict[str, Type["{class_name}"]] = {{}}
    
    @classmethod
    def register(cls, name: str, implementation: Type["{class_name}"]) -> None:
        """Register a new implementation."""
        cls._registry[name] = implementation
    
    @classmethod
    def create(cls, factory_type: str, **kwargs: Any) -> "{class_name}":
        """Create a new instance of the specified type."""
        if factory_type not in cls._registry:
            raise ValueError(f"Unknown factory type: {{factory_type}}")
        return cls._registry[factory_type](**kwargs)
    
    @classmethod
    def list_types(cls) -> list[str]:
        """List all registered factory types."""
        return list(cls._registry.keys())
'''

        output_path = Path(output_file)

        # Backup if the file exists
        if context.backup and output_path.exists():
            backup_path = output_path.with_suffix(".py.bak")
            backup_path.write_text(
                output_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            logger.info(f"Created backup: {backup_path}")

        # Write the factory implementation
        if not context.dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(factory_code, encoding="utf-8")
            logger.info(f"Generated factory for {class_name} in {output_file}")
        else:
            logger.info(f"Would generate factory for {class_name} in {output_file}")

    except Exception as e:
        logger.error(f"Error generating factory: {e}")
