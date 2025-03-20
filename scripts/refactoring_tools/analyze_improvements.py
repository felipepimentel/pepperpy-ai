#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze the impact of the proposed improvements for PepperPy.

This script analyzes the current codebase structure and estimates the impact
of the proposed improvements.
"""

import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add the project root to the path to ensure imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Constants
DUPLICATE_CONCEPTS = [
    {
        "name": "Document Processing",
        "files": ["pepperpy/rag/document.py", "pepperpy/rag/document/"],
        "impact": "Medium",
    },
    {
        "name": "Pipeline",
        "files": [
            "pepperpy/rag/pipeline.py",
            "pepperpy/rag/pipeline/",
            "pepperpy/core/utils.py",
            "pepperpy/core/composition.py",
            "pepperpy/data/transform.py",
        ],
        "impact": "High",
    },
    {
        "name": "Registry",
        "files": [
            "pepperpy/registry.py",
            "pepperpy/core/registry.py",
            "pepperpy/llm/registry.py",
            "pepperpy/providers/registry.py",
        ],
        "impact": "High",
    },
    {
        "name": "Capabilities",
        "files": ["pepperpy/capabilities.py", "pepperpy/core/capabilities.py"],
        "impact": "Medium",
    },
    {
        "name": "Configuration",
        "files": [
            "pepperpy/config.py",
            "pepperpy/core/config.py",
            "pepperpy/infra/config.py",
        ],
        "impact": "Medium",
    },
    {
        "name": "Providers Base",
        "files": ["pepperpy/providers/base.py", "pepperpy/core/providers.py"],
        "impact": "Medium",
    },
]

STRUCTURAL_IMPROVEMENTS = [
    {
        "name": "Core vs. Root",
        "description": "Move core concepts from root to core/ directory",
        "impact": "High",
    },
    {
        "name": "Utils Consolidation",
        "description": "Consolidate utility functions in a structured manner",
        "impact": "Medium",
    },
    {
        "name": "Infra vs. Core",
        "description": "Clear separation between infrastructure and core components",
        "impact": "Medium",
    },
    {
        "name": "Pipeline Framework",
        "description": "Unified pipeline framework for all pipeline types",
        "impact": "High",
    },
    {
        "name": "Public API",
        "description": "Clearly defined public API through proper exports",
        "impact": "High",
    },
]


def analyze_files() -> Dict[str, int]:
    """
    Analyze the codebase to count files per directory.

    Returns:
        Dict mapping directory paths to file counts
    """
    result = defaultdict(int)

    for root, dirs, files in os.walk(Path(project_root) / "pepperpy"):
        # Skip hidden directories and __pycache__
        if (
            any(part.startswith(".") for part in Path(root).parts)
            or "__pycache__" in root
        ):
            continue

        # Count Python files
        py_files = [f for f in files if f.endswith(".py")]
        if py_files:
            rel_path = os.path.relpath(root, project_root)
            result[rel_path] = len(py_files)

    return result


def analyze_duplicates() -> Dict[str, List[Dict]]:
    """
    Analyze the duplicate concepts and their impact.

    Returns:
        Dict with analysis results
    """
    # Count lines of code in each file
    lines_by_file = {}

    for concept in DUPLICATE_CONCEPTS:
        for file_path in concept["files"]:
            # Handle directories vs files
            if file_path.endswith("/"):
                # It's a directory
                dir_path = os.path.join(project_root, file_path)
                if os.path.isdir(dir_path):
                    for root, _, files in os.walk(dir_path):
                        for file in files:
                            if file.endswith(".py"):
                                full_path = os.path.join(root, file)
                                with open(full_path, "r") as f:
                                    lines_by_file[full_path] = len(f.readlines())
            else:
                # It's a file
                full_path = os.path.join(project_root, file_path)
                if os.path.isfile(full_path):
                    with open(full_path, "r") as f:
                        lines_by_file[full_path] = len(f.readlines())

    # Prepare results
    results = {}

    # Calculate total lines and files affected
    total_lines = sum(lines_by_file.values())
    total_files = len(lines_by_file)

    # Analyze each concept
    concept_details = []
    for concept in DUPLICATE_CONCEPTS:
        concept_lines = 0
        concept_files = 0

        for file_path in concept["files"]:
            # Handle directories vs files
            if file_path.endswith("/"):
                # It's a directory
                dir_path = os.path.join(project_root, file_path)
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith(".py"):
                            full_path = os.path.join(root, file)
                            if full_path in lines_by_file:
                                concept_lines += lines_by_file[full_path]
                                concept_files += 1
            else:
                # It's a file
                full_path = os.path.join(project_root, file_path)
                if full_path in lines_by_file:
                    concept_lines += lines_by_file[full_path]
                    concept_files += 1

        # Calculate percentage of codebase affected
        percentage = (concept_lines / total_lines * 100) if total_lines > 0 else 0

        concept_details.append({
            "name": concept["name"],
            "files": concept_files,
            "lines": concept_lines,
            "percentage": round(percentage, 2),
            "impact": concept["impact"],
        })

    # Sort by impact and lines
    concept_details.sort(key=lambda x: (x["impact"], x["lines"]), reverse=True)

    results["duplicate_concepts"] = concept_details
    results["total_files"] = total_files
    results["total_lines"] = total_lines

    return results


def generate_report() -> str:
    """
    Generate a markdown report with the analysis results.

    Returns:
        The report as a markdown string
    """
    directory_analysis = analyze_files()
    duplicate_analysis = analyze_duplicates()

    report = [
        "# PepperPy Improvement Analysis Report",
        "",
        "## Overview",
        "",
        f"Total Python files in the codebase: {sum(directory_analysis.values())}",
        f"Total directories with Python files: {len(directory_analysis)}",
        f"Files affected by duplicate concepts: {duplicate_analysis['total_files']}",
        f"Lines of code in affected files: {duplicate_analysis['total_lines']}",
        "",
        "## Duplicate Concepts Analysis",
        "",
        "| Concept | Files Affected | Lines of Code | % of Codebase | Impact |",
        "|---------|---------------|---------------|---------------|--------|",
    ]

    for concept in duplicate_analysis["duplicate_concepts"]:
        report.append(
            f"| {concept['name']} | {concept['files']} | {concept['lines']} | "
            f"{concept['percentage']}% | {concept['impact']} |"
        )

    report.extend([
        "",
        "## Structural Improvements",
        "",
        "| Improvement | Description | Impact |",
        "|-------------|-------------|--------|",
    ])

    for improvement in STRUCTURAL_IMPROVEMENTS:
        report.append(
            f"| {improvement['name']} | {improvement['description']} | "
            f"{improvement['impact']} |"
        )

    report.extend([
        "",
        "## Directory Analysis",
        "",
        "Top directories by number of Python files:",
        "",
        "| Directory | Python Files |",
        "|-----------|--------------|",
    ])

    # Sort directories by file count and show top 10
    sorted_dirs = sorted(directory_analysis.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]

    for dir_path, count in sorted_dirs:
        report.append(f"| {dir_path} | {count} |")

    report.extend([
        "",
        "## Conclusion",
        "",
        "The analysis indicates significant opportunities for improvement in the PepperPy codebase:",
        "",
        "1. **Duplicate Concepts**: Several key concepts have multiple implementations across the codebase.",
        "2. **Structural Issues**: The boundary between core components and domain-specific components is not clear.",
        "3. **API Structure**: The public API could be more clearly defined and organized.",
        "",
        "Implementing the proposed changes would lead to:",
        "",
        "- Reduced code duplication",
        "- Improved maintainability",
        "- Clearer API boundaries",
        "- Better developer experience",
        "",
        "The recommended approach is to proceed with the consolidation of duplicate modules first,",
        "followed by a reorganization of the core components and improvement of the public API.",
    ])

    return "\n".join(report)


def main():
    """Main function to generate and save the report."""
    report = generate_report()

    # Ensure reports directory exists
    reports_dir = os.path.join(project_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Save the report
    report_path = os.path.join(reports_dir, "improvement_analysis.md")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"Report generated: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
