"""Minimal repository analysis test."""

import asyncio
import os
from pathlib import Path
from typing import Any


async def analyze_structure(repo_path: str) -> dict[str, Any]:
    """Analyze repository structure.

    Args:
        repo_path: Path to the repository

    Returns:
        Structure analysis results
    """
    # Get path object
    path = Path(repo_path)

    # Get file counts
    file_count = 0
    extension_counts = {}
    directories = set()
    files = []

    print(f"Analyzing structure at {path}")

    # Walk directory
    for item in path.glob("**/*"):
        # Skip hidden files/dirs
        if any(part.startswith(".") for part in item.parts):
            continue

        if item.is_file():
            file_count += 1

            # Count by extension
            ext = item.suffix
            extension_counts[ext] = extension_counts.get(ext, 0) + 1

            # Add to files list
            rel_path = str(item.relative_to(path))
            files.append({
                "path": rel_path,
                "size": item.stat().st_size,
                "extension": ext,
            })

        elif item.is_dir():
            rel_path = str(item.relative_to(path))
            directories.add(rel_path)

    # Get top-level directories
    top_dirs = [d for d in directories if "/" not in d and d]

    return {
        "status": "success",
        "directory_count": len(directories),
        "file_count": file_count,
        "extension_counts": extension_counts,
        "top_directories": top_dirs,
        "files": files[:10],  # Just return first 10 files
    }


async def analyze_python_files(
    repo_path: str, pattern: str = "**/*.py"
) -> dict[str, Any]:
    """Analyze Python files in the repository.

    Args:
        repo_path: Path to the repository
        pattern: File pattern to match

    Returns:
        Python file analysis results
    """
    # Get path object
    path = Path(repo_path)

    # Find Python files
    python_files = list(path.glob(pattern))

    print(f"Found {len(python_files)} Python files")

    # Analyze files
    file_analysis = {}
    for py_file in python_files[:5]:  # Limit to 5 files for demo
        try:
            with open(py_file) as f:
                content = f.readlines()

            # Count lines
            total_lines = len(content)
            empty_lines = sum(1 for line in content if not line.strip())
            comment_lines = sum(1 for line in content if line.strip().startswith("#"))
            code_lines = total_lines - empty_lines - comment_lines

            # Count functions and classes
            function_count = sum(
                1 for line in content if line.strip().startswith("def ")
            )
            class_count = sum(
                1 for line in content if line.strip().startswith("class ")
            )

            # Store results
            rel_path = str(py_file.relative_to(path))
            file_analysis[rel_path] = {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "empty_lines": empty_lines,
                "comment_lines": comment_lines,
                "function_count": function_count,
                "class_count": class_count,
            }

        except Exception as e:
            rel_path = str(py_file.relative_to(path))
            file_analysis[rel_path] = {"error": str(e)}

    return {
        "status": "success",
        "analyzed_files": len(file_analysis),
        "total_files": len(python_files),
        "file_analysis": file_analysis,
    }


async def main() -> None:
    """Run the analysis."""
    # Get current directory
    current_dir = os.getcwd()

    # Analyze structure
    print("\n🔍 REPOSITORY STRUCTURE ANALYSIS\n")
    structure = await analyze_structure(current_dir)

    # Print structure summary
    print("\n📁 Structure summary:")
    print(f"  Directories: {structure['directory_count']}")
    print(f"  Files: {structure['file_count']}")
    print("\n📊 File types:")
    for ext, count in structure["extension_counts"].items():
        print(f"  {ext or 'no extension'}: {count}")
    print("\n📂 Top directories:")
    for dir_name in structure["top_directories"]:
        print(f"  {dir_name}")
    print("\n📄 Sample files:")
    for file in structure["files"][:5]:
        print(f"  {file['path']} ({file['size']} bytes)")

    # Analyze Python files in the plugins directory
    print("\n\n🔍 PYTHON CODE ANALYSIS\n")
    pattern = "plugins/workflow/**/*.py"
    python_analysis = await analyze_python_files(current_dir, pattern)

    # Print Python analysis
    print(
        f"\n📊 Python analysis (showing {len(python_analysis['file_analysis'])} of {python_analysis['total_files']} files):"
    )
    for path, metrics in python_analysis["file_analysis"].items():
        print(f"\n  📝 {path}:")
        if "error" in metrics:
            print(f"    ❌ Error: {metrics['error']}")
        else:
            print(
                f"    Lines: {metrics['total_lines']} total, {metrics['code_lines']} code, {metrics['comment_lines']} comments, {metrics['empty_lines']} empty"
            )
            print(
                f"    Contains: {metrics['function_count']} functions, {metrics['class_count']} classes"
            )


if __name__ == "__main__":
    asyncio.run(main())
