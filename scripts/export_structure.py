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
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any

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
    "venv",
    ".venv",
    "build",
    "dist",
    "*.egg-info",
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
}


def should_ignore(path: Path) -> bool:
    """Check if a path should be ignored.

    Args:
        path: Path to check

    Returns:
        True if the path should be ignored, False otherwise
    """
    # Check if any part of the path is in IGNORE_DIRS
    for part in path.parts:
        if any(part == ignore or (ignore.startswith("*") and part.endswith(ignore[1:])) for ignore in IGNORE_DIRS):
            return True

    # Check if the file name is in IGNORE_FILES
    if path.is_file():
        if any(path.name == ignore or (ignore.startswith("*") and path.name.endswith(ignore[1:])) for ignore in IGNORE_FILES):
            return True

    return False


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
        if file_path.suffix in {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sh"}:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
            except UnicodeDecodeError:
                # Not a text file
                pass

        return {
            "name": file_path.name,
            "path": str(file_path.relative_to(PROJECT_ROOT)),
            "size": size,
            "size_human": f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} bytes",
            "lines": line_count,
            "type": "file",
            "extension": file_path.suffix[1:] if file_path.suffix else "",
        }
    except Exception as e:
        logger.error(f"Error getting info for {file_path}: {e}")
        return {
            "name": file_path.name,
            "path": str(file_path.relative_to(PROJECT_ROOT)),
            "error": str(e),
            "type": "file",
        }


def get_dir_info(dir_path: Path, max_depth: Optional[int] = None, current_depth: int = 0) -> Dict[str, Any]:
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

        return {
            "name": dir_path.name,
            "path": str(dir_path.relative_to(PROJECT_ROOT)),
            "type": "directory",
            "contents": contents,
            "files_count": files_count,
            "dirs_count": dirs_count,
            "total_size": total_size,
            "total_size_human": f"{total_size / 1024:.1f} KB" if total_size >= 1024 else f"{total_size} bytes",
            "total_lines": total_lines,
        }
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
        result.append(f"{indent_str}📁 {structure['name']} ({structure['files_count']} files, {structure['dirs_count']} dirs, {structure['total_size_human']})")

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
        result.append(f"{indent_str}- **{structure['name']}/** ({structure['files_count']} files, {structure['dirs_count']} dirs, {structure['total_size_human']})")

        if structure.get("truncated"):
            result.append(f"{indent_str}  - ... (truncated)")
        else:
            # First list directories
            for item in [i for i in structure.get("contents", []) if i["type"] == "directory"]:
                result.append(format_markdown(item, indent + 1))

            # Then list files
            for item in [i for i in structure.get("contents", []) if i["type"] == "file"]:
                size_info = f", {item['size_human']}"
                lines_info = f", {item['lines']} lines" if item.get("lines") else ""
                result.append(f"{indent_str}  - {item['name']}{size_info}{lines_info}")

    return "\n".join(result)


def main() -> int:
    """Main function.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Export project structure")
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown", "yaml"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        help="Output file path",
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

    try:
        # Resolve directory path
        dir_path = Path(args.dir).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Directory not found: {dir_path}")
            return 1

        # Export structure
        export_structure(
            dir_path,
            args.format,
            args.output,
            args.max_depth,
        )

        return 0
    except Exception as e:
        logger.error(f"Error exporting structure: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 