#!/usr/bin/env python3
"""Script para exportar a estrutura do projeto PepperPy.

Este script analisa a estrutura do projeto e exporta para diferentes formatos:
- Texto simples
- JSON
- Markdown
- YAML

Pode ser usado independentemente ou como parte do analisador de código unificado.
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml


# ANSI color codes for terminal output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("export_structure")

# Define the project root
PROJECT_ROOT = Path(__file__).parent.parent

# Directories to ignore
IGNORE_DIRS = {
    "__pycache__",
    ".git",
    ".github",
    ".vscode",
    ".idea",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "build",
    "dist",
    "*.egg-info",
    "node_modules",
    ".ipynb_checkpoints",
    ".coverage",
    ".tox",
    ".eggs",
    ".cache",
    ".hypothesis",
    ".benchmarks",
    "__pypackages__",
    ".coverage-reports",
    ".htmlcov",
    ".nox",
    ".pytype",
    ".pepper_hub",
}

# Files to ignore
IGNORE_FILES = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.exe",
    ".DS_Store",
    "Thumbs.db",
    "*.swp",
    "*.swo",
    "*~",
    "*.bak",
    "*.tmp",
    "*.log",
    "*.coverage",
    "*.prof",
    "*.lprof",
    "*.pid",
    "*.retry",
    "*.orig",
    "*.rej",
    ".coverage",
    ".coverage.*",
    "coverage.xml",
    "*.cover",
}


# Check if running in a terminal that supports colors
def supports_color() -> bool:
    """Check if the terminal supports colors."""
    if os.environ.get("TERM") == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# Print colored text if supported
def print_color(text: str, color: str) -> None:
    """Print colored text if the terminal supports it."""
    if supports_color():
        print(f"{color}{text}{Colors.NC}")
    else:
        print(text)


# Check if running in a virtual environment
def check_virtual_env() -> None:
    """Check if running in a virtual environment and print a warning if not."""
    if not os.environ.get("VIRTUAL_ENV"):
        print_color("Warning: Not in a virtual environment", Colors.YELLOW)
        print("It's recommended to activate your virtual environment first")
        print("")


def should_ignore(path: Path) -> bool:
    """Check if a path should be ignored.

    Args:
        path: Path to check

    Returns:
        True if the path should be ignored, False otherwise
    """
    # Check if any part of the path is in IGNORE_DIRS
    for part in path.parts:
        if any(
            part == ignore or (ignore.startswith("*") and part.endswith(ignore[1:]))
            for ignore in IGNORE_DIRS
        ):
            return True

    # Check if the file name is in IGNORE_FILES
    if path.is_file():
        if any(
            path.name == ignore
            or (ignore.startswith("*") and path.name.endswith(ignore[1:]))
            for ignore in IGNORE_FILES
        ):
            return True

    return False


def extract_description(file_path: Path) -> Optional[str]:
    """Extract description from a file.

    For Python files, extracts the module docstring.
    For other files, extracts the first comment block.

    Args:
        file_path: Path to the file

    Returns:
        Description string or None if no description found
    """
    if not file_path.is_file():
        return None

    # Skip binary files and very large files
    try:
        if file_path.stat().st_size > 1024 * 1024:  # Skip files larger than 1MB
            return None

        # Handle Python files - extract docstring
        if file_path.suffix == ".py":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for module docstring
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                docstring = docstring_match.group(1).strip()
                # Return first line or first sentence if multiline
                if "\n" in docstring:
                    first_line = docstring.split("\n")[0].strip()
                    if first_line:
                        return first_line
                    # If first line is empty, try to get first sentence from any line
                    for line in docstring.split("\n"):
                        line = line.strip()
                        if line:
                            # Try to get first sentence
                            sentence_match = re.match(r"^(.*?[.!?])(?:\s|$)", line)
                            if sentence_match:
                                return sentence_match.group(1)
                            return line[:100] + ("..." if len(line) > 100 else "")
                else:
                    # Try to get first sentence from single line
                    sentence_match = re.match(r"^(.*?[.!?])(?:\s|$)", docstring)
                    if sentence_match:
                        return sentence_match.group(1)
                    return docstring[:100] + ("..." if len(docstring) > 100 else "")

        # For other text files, extract first comment block
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[:20]  # Read first 20 lines

        comment_chars = {
            ".py": "#",
            ".sh": "#",
            ".js": "//",
            ".ts": "//",
            ".java": "//",
            ".c": "//",
            ".cpp": "//",
            ".h": "//",
            ".hpp": "//",
            ".rb": "#",
            ".php": "//",
            ".go": "//",
            ".rs": "//",
        }

        comment_char = comment_chars.get(file_path.suffix, "#")
        comment_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith(comment_char):
                comment_text = line[len(comment_char) :].strip()
                if comment_text:
                    comment_lines.append(comment_text)
            elif (
                comment_lines
            ):  # Stop at first non-comment line if we already have comments
                break
            else:  # Skip initial blank lines
                continue

        if comment_lines:
            # Join first few comment lines
            description = " ".join(comment_lines[:3])
            return description[:150] + ("..." if len(description) > 150 else "")

        return None
    except (UnicodeDecodeError, IOError):
        # Not a text file or can't be read
        return None


def extract_dir_description(dir_path: Path) -> Optional[str]:
    """Extract description for a directory from its __init__.py file.

    Args:
        dir_path: Path to the directory

    Returns:
        Description string or None if no description found
    """
    init_file = dir_path / "__init__.py"
    if init_file.exists() and init_file.is_file():
        return extract_description(init_file)
    return None


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get information about a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file information
    """
    try:
        size = file_path.stat().st_size
        line_count = 0

        # Count lines for text files
        if file_path.suffix in {
            ".py",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".sh",
        }:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
            except UnicodeDecodeError:
                # Not a text file
                pass

        # Extract description
        description = extract_description(file_path)

        result = {
            "name": file_path.name,
            "path": str(file_path.relative_to(PROJECT_ROOT)),
            "size": size,
            "size_human": f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} bytes",
            "lines": line_count,
            "type": "file",
            "extension": file_path.suffix[1:] if file_path.suffix else "",
        }

        if description:
            result["description"] = description

        return result
    except Exception as e:
        logger.error(f"Error getting info for {file_path}: {e}")
        return {
            "name": file_path.name,
            "path": str(file_path.relative_to(PROJECT_ROOT)),
            "error": str(e),
            "type": "file",
        }


def get_dir_info(
    dir_path: Path, max_depth: Optional[int] = None, current_depth: int = 0
) -> Dict[str, Any]:
    """Get information about a directory and its contents.

    Args:
        dir_path: Path to the directory
        max_depth: Maximum depth to traverse
        current_depth: Current depth

    Returns:
        Dictionary with directory information
    """
    if max_depth is not None and current_depth > max_depth:
        return {
            "name": dir_path.name,
            "path": str(dir_path.relative_to(PROJECT_ROOT)),
            "type": "directory",
            "truncated": True,
        }

    try:
        contents = []
        files_count = 0
        dirs_count = 0
        total_size = 0
        total_lines = 0

        # Process all files and directories
        for item in sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name)):
            if should_ignore(item):
                continue

            if item.is_file():
                file_info = get_file_info(item)
                contents.append(file_info)
                files_count += 1
                total_size += file_info.get("size", 0)
                total_lines += file_info.get("lines", 0)
            elif item.is_dir():
                dir_info = get_dir_info(item, max_depth, current_depth + 1)
                contents.append(dir_info)
                dirs_count += 1
                total_size += dir_info.get("size", 0)
                total_lines += dir_info.get("lines", 0)

        # Extract directory description from __init__.py
        description = extract_dir_description(dir_path)

        result = {
            "name": dir_path.name,
            "path": str(dir_path.relative_to(PROJECT_ROOT)),
            "type": "directory",
            "contents": contents,
            "files_count": files_count,
            "dirs_count": dirs_count,
            "total_size": total_size,
            "total_size_human": f"{total_size / 1024:.1f} KB"
            if total_size >= 1024
            else f"{total_size} bytes",
            "total_lines": total_lines,
        }

        if description:
            result["description"] = description

        return result
    except Exception as e:
        logger.error(f"Error getting info for {dir_path}: {e}")
        return {
            "name": dir_path.name,
            "path": str(dir_path.relative_to(PROJECT_ROOT)),
            "error": str(e),
            "type": "directory",
        }


def export_structure(
    root_dir: Path,
    output_format: str = "text",
    output_file: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> None:
    """Export the project structure.

    Args:
        root_dir: Root directory of the project
        output_format: Output format (text, json, markdown, yaml)
        output_file: Output file path
        max_depth: Maximum depth to traverse
    """
    logger.info(f"Exporting project structure in {output_format} format...")

    # Get project structure
    structure = get_dir_info(root_dir, max_depth)

    # Format output
    if output_format == "json":
        output = json.dumps(structure, indent=2)
    elif output_format == "yaml":
        output = yaml.dump(structure, default_flow_style=False)
    elif output_format == "markdown":
        output = format_markdown(structure)
    else:  # text
        output = format_text(structure)

    # Write output
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        logger.info(f"Project structure exported to {output_file}")
    else:
        print(output)


def format_text(structure: Dict[str, Any], indent: int = 0) -> str:
    """Format structure as text.

    Args:
        structure: Structure dictionary
        indent: Current indentation level

    Returns:
        Formatted text
    """
    result = []
    indent_str = "  " * indent

    if structure["type"] == "directory":
        result.append(
            f"{indent_str}📁 {structure['name']} ({structure['files_count']} files, {structure['dirs_count']} dirs, {structure['total_size_human']})"
        )

        if structure.get("truncated"):
            result.append(f"{indent_str}  ... (truncated)")
        else:
            for item in structure.get("contents", []):
                result.append(format_text(item, indent + 1))
    else:
        size_info = f", {structure['size_human']}"
        lines_info = f", {structure['lines']} lines" if structure.get("lines") else ""
        result.append(f"{indent_str}📄 {structure['name']}{size_info}{lines_info}")

    return "\n".join(result)


def format_markdown(structure: Dict[str, Any], indent: int = 0) -> str:
    """Format structure as Markdown.

    Args:
        structure: Structure dictionary
        indent: Current indentation level

    Returns:
        Formatted Markdown
    """
    result = []
    indent_str = "  " * indent

    if indent == 0:
        result.append("# Project Structure\n")
        result.append(f"- **Root Directory**: {structure['path']}")
        result.append(f"- **Files**: {structure['files_count']}")
        result.append(f"- **Directories**: {structure['dirs_count']}")
        result.append(f"- **Total Size**: {structure['total_size_human']}")
        result.append(f"- **Total Lines**: {structure['total_lines']}")
        result.append("\n## Directory Tree\n")

    if structure["type"] == "directory":
        result.append(
            f"{indent_str}- **{structure['name']}/** ({structure['files_count']} files, {structure['dirs_count']} dirs, {structure['total_size_human']})"
        )

        if structure.get("truncated"):
            result.append(f"{indent_str}  - ... (truncated)")
        else:
            # First list directories
            for item in [
                i for i in structure.get("contents", []) if i["type"] == "directory"
            ]:
                result.append(format_markdown(item, indent + 1))

            # Then list files
            for item in [
                i for i in structure.get("contents", []) if i["type"] == "file"
            ]:
                size_info = f", {item['size_human']}"
                lines_info = f", {item['lines']} lines" if item.get("lines") else ""
                result.append(f"{indent_str}  - {item['name']}{size_info}{lines_info}")

    return "\n".join(result)


def main() -> int:
    """Main function.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Print header
    print_color("PepperPy Structure Exporter", Colors.BLUE)
    print_color("=========================", Colors.YELLOW)
    print("")

    # Check virtual environment
    check_virtual_env()

    parser = argparse.ArgumentParser(description="Export project structure")
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "yaml"],
        default="yaml",
        help="Output format (default: yaml)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: .product/project_structure.yml if format is yaml)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        help="Maximum depth to traverse",
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="Directory to analyze (default: current directory)",
    )

    args = parser.parse_args()

    # Set default output path for YAML format if not specified
    if args.format == "yaml" and not args.output:
        args.output = ".product/project_structure.yml"

    try:
        # Resolve directory path
        dir_path = Path(args.dir).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Directory not found: {dir_path}")
            print_color(f"Error: Directory not found: {dir_path}", Colors.RED)
            return 1

        # Print export message
        print_color("Exporting project structure...", Colors.YELLOW)
        print("")

        # Export structure
        export_structure(
            dir_path,
            args.format,
            args.output,
            args.max_depth,
        )

        # Print success message
        if args.output:
            print_color(
                f"\nProject structure exported successfully to {args.output}!",
                Colors.GREEN,
            )
        else:
            print_color("\nProject structure exported successfully!", Colors.GREEN)

        return 0
    except Exception as e:
        logger.error(f"Error exporting structure: {e}")
        print_color(f"\nError exporting project structure: {e}", Colors.RED)
        return 1


if __name__ == "__main__":
    sys.exit(main())
