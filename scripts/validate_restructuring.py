#!/usr/bin/env python3
"""Script to validate the restructuring of the PepperPy project.

This script checks if the restructuring was successful by verifying:
1. If the directories were moved correctly
2. If compatibility stubs were created
3. If imports were updated correctly
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

# Define the expected directory structure after restructuring
EXPECTED_DIRECTORIES = [
    # Capabilities
    "pepperpy/capabilities/audio",
    "pepperpy/capabilities/vision",
    "pepperpy/capabilities/multimodal",
    # Providers
    "pepperpy/providers/llm",
    "pepperpy/providers/cloud",
    # Caching
    "pepperpy/caching",
]

# Define the expected compatibility stubs
EXPECTED_STUBS = [
    # Original directories with compatibility stubs
    "pepperpy/audio",
    "pepperpy/vision",
    "pepperpy/multimodal",
    "pepperpy/memory/cache.py",
]

# Define problematic imports that should not exist after restructuring
PROBLEMATIC_IMPORTS = [
    "from pepperpy.audio import",
    "import pepperpy.audio",
    "from pepperpy.vision import",
    "import pepperpy.vision",
    "from pepperpy.multimodal import",
    "import pepperpy.multimodal",
    "from pepperpy.memory.cache import",
    "import pepperpy.memory.cache",
]

# Diretórios e arquivos a serem ignorados na verificação de imports problemáticos
IGNORED_PATHS = [
    "scripts/",
    "backup/",
    ".git/",
    ".venv/",
    "__pycache__/",
]


def check_directories(project_root: Path) -> Tuple[List[str], List[str]]:
    """Check if the expected directories exist.

    Args:
        project_root: Path to the project root

    Returns:
        Tuple of (existing directories, missing directories)
    """
    existing = []
    missing = []

    for directory in EXPECTED_DIRECTORIES:
        dir_path = project_root / directory
        if dir_path.exists() and dir_path.is_dir():
            existing.append(directory)
        else:
            missing.append(directory)

    return existing, missing


def check_stubs(project_root: Path) -> Tuple[List[str], List[str]]:
    """Check if the expected compatibility stubs exist.

    Args:
        project_root: Path to the project root

    Returns:
        Tuple of (existing stubs, missing stubs)
    """
    existing = []
    missing = []

    for stub in EXPECTED_STUBS:
        stub_path = project_root / stub

        # Check if it's a directory with __init__.py
        if stub_path.is_dir() and (stub_path / "__init__.py").exists():
            with open(stub_path / "__init__.py", "r", encoding="utf-8") as f:
                content = f.read()
                if "Compatibility stub" in content:
                    existing.append(stub)
                else:
                    missing.append(stub)
        # Check if it's a file
        elif stub_path.is_file():
            with open(stub_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "Compatibility stub" in content:
                    existing.append(stub)
                else:
                    missing.append(stub)
        else:
            missing.append(stub)

    return existing, missing


def should_ignore_path(path: str) -> bool:
    """Check if a path should be ignored in the validation.

    Args:
        path: Path to check

    Returns:
        True if the path should be ignored, False otherwise
    """
    for ignored_path in IGNORED_PATHS:
        if path.startswith(ignored_path):
            return True
    return False


def find_problematic_imports(project_root: Path) -> Dict[str, List[str]]:
    """Find files with problematic imports.

    Args:
        project_root: Path to the project root

    Returns:
        Dictionary mapping problematic imports to lists of files
    """
    problematic_files: Dict[str, List[str]] = {imp: [] for imp in PROBLEMATIC_IMPORTS}

    # Skip directories
    skip_dirs = {".git", ".venv", "backup", "__pycache__", "scripts"}

    for root, dirs, files in os.walk(project_root):
        # Skip specified directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(project_root))

                # Skip ignored paths
                if should_ignore_path(rel_path):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    for imp in PROBLEMATIC_IMPORTS:
                        if imp in content:
                            # Check if it's not in a compatibility stub
                            with open(file_path, "r", encoding="utf-8") as f:
                                first_lines = "".join(f.readlines()[:5])
                                if "Compatibility stub" not in first_lines:
                                    problematic_files[imp].append(rel_path)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return problematic_files


def main():
    """Main function."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    print("Validating PepperPy restructuring...")
    print("=" * 50)

    # Check directories
    existing_dirs, missing_dirs = check_directories(project_root)
    print("\n1. Directory Structure Check:")
    print(f"   - {len(existing_dirs)} expected directories exist")
    if missing_dirs:
        print(f"   - {len(missing_dirs)} expected directories are missing:")
        for directory in missing_dirs:
            print(f"     - {directory}")
    else:
        print("   - All expected directories exist")

    # Check stubs
    existing_stubs, missing_stubs = check_stubs(project_root)
    print("\n2. Compatibility Stubs Check:")
    print(f"   - {len(existing_stubs)} expected compatibility stubs exist")
    if missing_stubs:
        print(f"   - {len(missing_stubs)} expected compatibility stubs are missing:")
        for stub in missing_stubs:
            print(f"     - {stub}")
    else:
        print("   - All expected compatibility stubs exist")

    # Check imports
    problematic_imports = find_problematic_imports(project_root)
    total_problematic = sum(len(files) for files in problematic_imports.values())
    print("\n3. Import Check:")
    if total_problematic > 0:
        print(f"   - Found {total_problematic} problematic imports:")
        for imp, files in problematic_imports.items():
            if files:
                print(f"     - '{imp}' found in {len(files)} files:")
                for file in files[:5]:  # Show only first 5 files
                    print(f"       - {file}")
                if len(files) > 5:
                    print(f"       - ... and {len(files) - 5} more files")
    else:
        print("   - No problematic imports found")

    # Overall result
    print("\nOverall Validation Result:")
    if not missing_dirs and not missing_stubs and total_problematic == 0:
        print("✅ Restructuring validation PASSED")
    else:
        print("❌ Restructuring validation FAILED")
        if missing_dirs:
            print(f"   - {len(missing_dirs)} directories are missing")
        if missing_stubs:
            print(f"   - {len(missing_stubs)} compatibility stubs are missing")
        if total_problematic > 0:
            print(f"   - {total_problematic} problematic imports found")


if __name__ == "__main__":
    main()
