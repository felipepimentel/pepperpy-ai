#!/usr/bin/env python3
"""Export project structure in a simplified format for LLM context.

This script exports the project structure in a simplified format that can be used
as context for language models. The output is designed to be easily parsed and
understood by AI models.

Component: Development Tools
Created: 2024-03-20
Task: TASK-000
Status: active
"""

import re
from pathlib import Path
from typing import Any

import yaml


def extract_module_description(init_file: Path) -> str:
    """Extract module description from __init__.py docstring."""
    if not init_file.exists():
        return ""

    try:
        with open(init_file) as f:
            content = f.read()
            # Try to extract full docstring
            full_docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if full_docstring:
                # Get first paragraph and clean it
                desc = full_docstring.group(1).strip().split("\n\n")[0]
                desc = " ".join(line.strip() for line in desc.splitlines())
                desc = desc.strip('"').strip(".")  # Remove quotes and trailing dot
                return desc or "Module initialization"

    except Exception:
        pass
    return "Module initialization"


def should_ignore(path: str) -> bool:
    """Check if path should be ignored."""
    ignore_patterns = [
        r"__pycache__",
        r"\.pytest_cache",
        r"\.mypy_cache",
        r"\.coverage",
        r"\.env",
        r"\.venv",
        r"\.idea",
        r"\.vscode",
        r"\.DS_Store",
        r"\.git",
        r"\.",  # Any hidden file/directory
        r".*\.pyc$",
        r".*\.pyo$",
        r".*\.pyd$",
    ]
    return any(re.search(pattern, path) for pattern in ignore_patterns)


def get_module_files(module_path: Path) -> list[dict[str, str]]:
    """Get list of module files with descriptions."""
    files = []

    # Process Python files
    for file in sorted(module_path.glob("*.py")):
        try:
            with open(file) as f:
                content = f.read()
                docstring_match = re.search(
                    r'"""(.*?)(?:\n\n|\n|""")', content, re.DOTALL
                )
                if docstring_match:
                    desc = docstring_match.group(1).strip()
                    desc = " ".join(line.strip() for line in desc.splitlines())
                    desc = desc.strip('"').strip(".")
                else:
                    # Generate meaningful description from filename
                    stem = file.stem
                    if stem == "__init__":
                        desc = "Module initialization and exports"
                    else:
                        # Convert snake_case to Title Case
                        words = stem.split("_")
                        desc = f"{' '.join(word.title() for word in words)} module"

                files.append({file.name: desc})
        except Exception:
            # Fallback to basic description
            files.append({file.name: f"{file.stem.title()} module"})

    return sorted(
        files, key=lambda x: list(x.keys())[0] != "__init__.py"
    )  # __init__.py first


def export_structure(
    root_dir: Path,
    current_depth: int = 0,
    max_depth: int = 5,
    module_path: list[str] | None = None,
) -> dict[str, Any]:
    """Export directory structure with descriptions from project specification."""
    if current_depth > max_depth or should_ignore(str(root_dir)):
        return {}

    if module_path is None:
        module_path = []

    structure: dict[str, Any] = {
        "description": extract_module_description(root_dir / "__init__.py")
    }

    # Process subdirectories (modules)
    modules = {}
    for path in sorted(root_dir.iterdir()):
        if path.is_dir() and not should_ignore(str(path)):
            current_module = module_path + [path.name]
            module_struct = export_structure(
                path, current_depth + 1, max_depth, current_module
            )
            if module_struct:
                modules[path.name] = module_struct

    if modules:
        structure["modules"] = modules

    # Process files
    files = get_module_files(root_dir)
    if files:
        structure["files"] = files

    return structure


def generate_yaml(structure: dict[str, Any]) -> str:
    """Generate YAML structure with proper formatting."""
    return yaml.dump(
        structure,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        indent=2,
    )


def main() -> None:
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    pepperpy_dir = project_root / "pepperpy"

    if not pepperpy_dir.exists():
        print("Error: pepperpy directory not found!")
        return

    # Generate structure
    structure = {
        "version": "2.0",
        "name": "pepperpy",
        "description": "Framework modular para construção de aplicações baseadas em IA",
        "structure": {"pepperpy": export_structure(pepperpy_dir)},
    }

    # Generate and save YAML
    yaml_content = generate_yaml(structure)
    output_path = project_root / ".product" / "project_structure.yml"

    with open(output_path, "w") as f:
        f.write(yaml_content)

    print(f"\nProject structure exported to: {output_path}")
    print("\nStructure includes:")
    print("- Module descriptions from __init__.py docstrings")
    print("- File listings with descriptions")


if __name__ == "__main__":
    main()
