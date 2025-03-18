#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze code quality metrics for the PepperPy codebase.

This script analyzes various aspects of code quality including:
- Cyclomatic complexity
- Method length
- Class cohesion
- Comment ratio
- Function argument count
- Error handling
"""

import ast
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Constants
MAX_COMPLEXITY = 10
MAX_METHOD_LENGTH = 50
MAX_ARGS = 5
MIN_COMMENT_RATIO = 0.1


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor that calculates the cyclomatic complexity of a function."""

    def __init__(self):
        self.complexity = 1  # Start at 1 for the function itself

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.complexity += len(node.handlers)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # 'and' and 'or' operators add complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class FunctionAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes functions for quality metrics."""

    def __init__(self):
        self.functions = []

    def visit_FunctionDef(self, node):
        self.analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.analyze_function(node)
        self.generic_visit(node)

    def analyze_function(self, node):
        # Get the function name
        function_name = node.name

        # Calculate cyclomatic complexity
        complexity_visitor = ComplexityVisitor()
        complexity_visitor.visit(node)
        complexity = complexity_visitor.complexity

        # Calculate function length (number of lines)
        function_length = (node.end_lineno - node.lineno + 1) if hasattr(node, 'end_lineno') and node.end_lineno is not None else 0

        # Count number of arguments
        arg_count = len(node.args.args)

        # Check for docstring
        docstring = ast.get_docstring(node)
        has_docstring = docstring is not None

        # Count number of return statements
        return_visitor = ReturnVisitor()
        return_visitor.visit(node)
        return_count = return_visitor.count

        # Count comment lines (approximation)
        source_lines = []
        for i in range(
            node.lineno,
            node.end_lineno + 1 if hasattr(node, "end_lineno") else node.lineno + 20,
        ):
            try:
                # This is a hacky way to get the source lines, would need source code
                source_lines.append("")
            except IndexError:
                break

        comment_lines = sum(1 for line in source_lines if line.strip().startswith("#"))
        comment_ratio = comment_lines / max(1, function_length)

        # Count exception handling
        exception_visitor = ExceptionVisitor()
        exception_visitor.visit(node)
        exception_count = exception_visitor.count

        # Store function info
        self.functions.append({
            "name": function_name,
            "complexity": complexity,
            "length": function_length,
            "arg_count": arg_count,
            "has_docstring": has_docstring,
            "return_count": return_count,
            "comment_ratio": comment_ratio,
            "exception_count": exception_count,
            "line": node.lineno,
        })


class ClassAnalyzer(ast.NodeVisitor):
    """AST visitor that analyzes classes for quality metrics."""

    def __init__(self):
        self.classes = []

    def visit_ClassDef(self, node):
        # Get the class name
        class_name = node.name

        # Calculate class length (number of lines)
        class_length = (
            (node.end_lineno - node.lineno + 1)
            if hasattr(node, "end_lineno") and node.end_lineno is not None
            else 0
        )

        # Check for docstring
        docstring = ast.get_docstring(node)
        has_docstring = docstring is not None

        # Count methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        # Calculate method count
        method_count = len(methods)

        # Calculate attributes (approximation)
        attributes = set()
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.add(target.id)

        attribute_count = len(attributes)

        # Store class info
        self.classes.append({
            "name": class_name,
            "length": class_length,
            "has_docstring": has_docstring,
            "method_count": method_count,
            "attribute_count": attribute_count,
            "methods": methods,
            "line": node.lineno,
        })

        # Continue visiting
        self.generic_visit(node)


class ReturnVisitor(ast.NodeVisitor):
    """AST visitor that counts return statements."""

    def __init__(self):
        self.count = 0

    def visit_Return(self, node):
        self.count += 1
        self.generic_visit(node)


class ExceptionVisitor(ast.NodeVisitor):
    """AST visitor that counts exception handling."""

    def __init__(self):
        self.count = 0

    def visit_Try(self, node):
        self.count += 1
        self.generic_visit(node)


def analyze_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Python file for code quality metrics.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        Dict containing analysis results
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        # Analyze functions
        function_analyzer = FunctionAnalyzer()
        function_analyzer.visit(tree)
        functions = function_analyzer.functions

        # Analyze classes
        class_analyzer = ClassAnalyzer()
        class_analyzer.visit(tree)
        classes = class_analyzer.classes

        # Calculate file-level metrics
        line_count = len(content.splitlines())

        # Calculate comment ratio (approximation)
        comment_lines = sum(
            1 for line in content.splitlines() if line.strip().startswith("#")
        )
        docstring_pattern = r'""".*?"""'
        docstring_matches = re.findall(docstring_pattern, content, re.DOTALL)
        docstring_lines = sum(len(match.splitlines()) for match in docstring_matches)

        comment_ratio = (comment_lines + docstring_lines) / max(1, line_count)

        # Calculate quality score
        quality_issues = []

        # Check function complexity
        for func in functions:
            if func["complexity"] > MAX_COMPLEXITY:
                quality_issues.append({
                    "type": "high_complexity",
                    "item": func["name"],
                    "value": func["complexity"],
                    "threshold": MAX_COMPLEXITY,
                    "line": func["line"],
                })

            if func["length"] > MAX_METHOD_LENGTH:
                quality_issues.append({
                    "type": "long_method",
                    "item": func["name"],
                    "value": func["length"],
                    "threshold": MAX_METHOD_LENGTH,
                    "line": func["line"],
                })

            if func["arg_count"] > MAX_ARGS:
                quality_issues.append({
                    "type": "too_many_args",
                    "item": func["name"],
                    "value": func["arg_count"],
                    "threshold": MAX_ARGS,
                    "line": func["line"],
                })

            if not func["has_docstring"]:
                quality_issues.append({
                    "type": "missing_docstring",
                    "item": func["name"],
                    "line": func["line"],
                })

        # Check class docstrings
        for cls in classes:
            if not cls["has_docstring"]:
                quality_issues.append({
                    "type": "missing_docstring",
                    "item": cls["name"],
                    "line": cls["line"],
                })

        # Check file comment ratio
        if comment_ratio < MIN_COMMENT_RATIO:
            quality_issues.append({
                "type": "low_comment_ratio",
                "value": comment_ratio,
                "threshold": MIN_COMMENT_RATIO,
            })

        return {
            "file_path": file_path,
            "line_count": line_count,
            "comment_ratio": comment_ratio,
            "function_count": len(functions),
            "class_count": len(classes),
            "functions": functions,
            "classes": classes,
            "quality_issues": quality_issues,
        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {
            "file_path": file_path,
            "error": str(e),
        }


def analyze_codebase(root_dir: str) -> Dict[str, Any]:
    """
    Analyze the entire codebase for code quality metrics.

    Args:
        root_dir: Root directory of the codebase

    Returns:
        Dict containing analysis results
    """
    results = {
        "files": [],
        "summary": {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "avg_complexity": 0,
            "avg_method_length": 0,
            "avg_comment_ratio": 0,
            "quality_issues": defaultdict(int),
        },
    }

    # Find all Python files
    python_files = []
    for root, _, files in os.walk(root_dir):
        # Skip hidden directories and __pycache__
        if (
            any(part.startswith(".") for part in Path(root).parts)
            or "__pycache__" in root
        ):
            continue

        # Skip directories that aren't part of the package
        if "pepperpy" not in root:
            continue

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    # Analyze each file
    total_complexity = 0
    total_method_length = 0
    total_functions = 0
    total_comment_ratio = 0

    for file in python_files:
        file_result = analyze_file(file)

        if "error" in file_result:
            continue

        results["files"].append(file_result)

        # Update summary
        results["summary"]["total_files"] += 1
        results["summary"]["total_lines"] += file_result["line_count"]
        results["summary"]["total_functions"] += file_result["function_count"]
        results["summary"]["total_classes"] += file_result["class_count"]

        # Update averages
        for func in file_result["functions"]:
            total_complexity += func["complexity"]
            total_method_length += func["length"]
            total_functions += 1

        total_comment_ratio += file_result["comment_ratio"]

        # Update quality issues
        for issue in file_result["quality_issues"]:
            results["summary"]["quality_issues"][issue["type"]] += 1

    # Calculate averages
    if total_functions > 0:
        results["summary"]["avg_complexity"] = total_complexity / total_functions
        results["summary"]["avg_method_length"] = total_method_length / total_functions

    if results["summary"]["total_files"] > 0:
        results["summary"]["avg_comment_ratio"] = (
            total_comment_ratio / results["summary"]["total_files"]
        )

    return results


def generate_report(results: Dict[str, Any]) -> str:
    """
    Generate a markdown report from analysis results.

    Args:
        results: Analysis results

    Returns:
        Markdown report
    """
    report = [
        "# PepperPy Code Quality Analysis",
        "",
        "## Summary",
        "",
        f"- **Files Analyzed**: {results['summary']['total_files']}",
        f"- **Total Lines of Code**: {results['summary']['total_lines']}",
        f"- **Total Functions**: {results['summary']['total_functions']}",
        f"- **Total Classes**: {results['summary']['total_classes']}",
        f"- **Average Cyclomatic Complexity**: {results['summary']['avg_complexity']:.2f}",
        f"- **Average Method Length**: {results['summary']['avg_method_length']:.2f} lines",
        f"- **Average Comment Ratio**: {results['summary']['avg_comment_ratio']:.2f}",
        "",
        "## Quality Issues",
        "",
    ]

    # Sort quality issues by count
    sorted_issues = sorted(
        results["summary"]["quality_issues"].items(), key=lambda x: x[1], reverse=True
    )

    for issue_type, count in sorted_issues:
        report.append(f"- **{issue_type.replace('_', ' ').title()}**: {count}")

    report.extend([
        "",
        "## Top Files by Complexity",
        "",
        "| File | Functions | Classes | Avg Complexity | Issues |",
        "|------|-----------|---------|----------------|--------|",
    ])

    # Sort files by complexity
    complexity_by_file = []
    for file in results["files"]:
        if not file["functions"]:
            continue

        avg_complexity = sum(func["complexity"] for func in file["functions"]) / len(
            file["functions"]
        )
        complexity_by_file.append((file["file_path"], avg_complexity, file))

    complexity_by_file.sort(key=lambda x: x[1], reverse=True)

    for file_path, avg_complexity, file in complexity_by_file[:10]:
        rel_path = os.path.relpath(file_path, project_root)
        report.append(
            f"| {rel_path} | {file['function_count']} | {file['class_count']} | "
            f"{avg_complexity:.2f} | {len(file['quality_issues'])} |"
        )

    report.extend([
        "",
        "## Top Complex Functions",
        "",
        "| Function | File | Complexity | Length | Args | Issues |",
        "|----------|------|------------|--------|------|--------|",
    ])

    # Find most complex functions
    complex_functions = []
    for file in results["files"]:
        for func in file["functions"]:
            complex_functions.append((func, file["file_path"]))

    complex_functions.sort(key=lambda x: x[0]["complexity"], reverse=True)

    for func, file_path in complex_functions[:10]:
        rel_path = os.path.relpath(file_path, project_root)
        issues = []

        if func["complexity"] > MAX_COMPLEXITY:
            issues.append("high_complexity")

        if func["length"] > MAX_METHOD_LENGTH:
            issues.append("long_method")

        if func["arg_count"] > MAX_ARGS:
            issues.append("too_many_args")

        if not func["has_docstring"]:
            issues.append("missing_docstring")

        report.append(
            f"| {func['name']} | {rel_path} | {func['complexity']} | "
            f"{func['length']} | {func['arg_count']} | {', '.join(issues)} |"
        )

    report.extend([
        "",
        "## Recommendations",
        "",
        "Based on this analysis, here are recommended areas for improvement:",
        "",
    ])

    # Generate recommendations based on findings
    if results["summary"]["avg_complexity"] > 5:
        report.append(
            "1. **Reduce Function Complexity**: Many functions have high cyclomatic complexity. Consider breaking down complex functions into smaller, more manageable pieces."
        )

    if results["summary"]["avg_method_length"] > 30:
        report.append(
            "2. **Shorten Methods**: Several methods are too long. Long methods are harder to understand and maintain."
        )

    if results["summary"]["avg_comment_ratio"] < 0.15:
        report.append(
            "3. **Improve Documentation**: The codebase has a low comment ratio. Consider adding more documentation, especially for complex logic."
        )

    if results["summary"]["quality_issues"].get("missing_docstring", 0) > 0:
        report.append(
            "4. **Add Missing Docstrings**: Several functions and classes are missing docstrings. Add docstrings to improve code readability and maintainability."
        )

    if results["summary"]["quality_issues"].get("too_many_args", 0) > 0:
        report.append(
            "5. **Reduce Function Parameters**: Some functions have too many parameters. Consider using parameter objects or breaking functions down."
        )

    return "\n".join(report)


def main():
    """Main function to analyze the codebase and generate a report."""
    print("Analyzing PepperPy codebase...")
    results = analyze_codebase(os.path.join(project_root, "pepperpy"))

    # Generate report
    report = generate_report(results)

    # Save report
    reports_dir = os.path.join(project_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    report_path = os.path.join(reports_dir, "code_quality_analysis.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Save raw results for further analysis
    results_path = os.path.join(reports_dir, "code_quality_data.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Analysis complete. Report saved to {report_path}")
    print(f"Raw data saved to {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
