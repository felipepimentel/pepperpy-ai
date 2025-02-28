#!/usr/bin/env python3
"""Script to check the coverage of compatibility stubs.

This script verifies if all modules that were moved during restructuring
have corresponding compatibility stubs.
"""

from pathlib import Path
from typing import Dict

# Define the modules that were moved during restructuring
MOVED_MODULES = {
    # Original location: New location
    "pepperpy/audio": "pepperpy/capabilities/audio",
    "pepperpy/vision": "pepperpy/capabilities/vision",
    "pepperpy/multimodal": "pepperpy/capabilities/multimodal",
    "pepperpy/llm/providers": "pepperpy/providers/llm",
    "pepperpy/rag/providers": "pepperpy/providers/rag",
    "pepperpy/cloud/providers": "pepperpy/providers/cloud",
    "pepperpy/memory/cache.py": "pepperpy/caching/memory_cache.py",
}


def find_stubs(project_root: Path) -> Dict[str, bool]:
    """Find compatibility stubs in the project.

    Args:
        project_root: Path to the project root

    Returns:
        Dictionary mapping module paths to boolean indicating if stub exists
    """
    stubs_status = {path: False for path in MOVED_MODULES}

    for original_path in MOVED_MODULES:
        path = project_root / original_path

        # Check if it's a directory with __init__.py
        if path.is_dir() and (path / "__init__.py").exists():
            with open(path / "__init__.py", "r", encoding="utf-8") as f:
                content = f.read()
                if "Compatibility stub" in content:
                    stubs_status[original_path] = True
        # Check if it's a file
        elif path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if "Compatibility stub" in content:
                    stubs_status[original_path] = True

    return stubs_status


def check_stub_imports(
    project_root: Path, stubs_status: Dict[str, bool]
) -> Dict[str, bool]:
    """Check if stubs correctly import from new locations.

    Args:
        project_root: Path to the project root
        stubs_status: Dictionary of stub status

    Returns:
        Dictionary mapping module paths to boolean indicating if imports are correct
    """
    imports_status = {path: False for path in stubs_status if stubs_status[path]}

    for original_path, exists in stubs_status.items():
        if not exists:
            continue

        new_path = MOVED_MODULES[original_path]
        path = project_root / original_path

        # Get the expected import statement
        if original_path.endswith(".py"):
            # For files, the import should be from the new module
            new_module = new_path.replace("/", ".").replace(".py", "")
            expected_import = f"from {new_module}"
        else:
            # For directories, the import should be from the new package
            new_package = new_path.replace("/", ".")
            expected_import = f"from {new_package}"

        # Check if the stub has the correct import
        if path.is_dir() and (path / "__init__.py").exists():
            with open(path / "__init__.py", "r", encoding="utf-8") as f:
                content = f.read()
                if expected_import in content or "import *" in content:
                    imports_status[original_path] = True
        elif path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if expected_import in content or "import *" in content:
                    imports_status[original_path] = True

    return imports_status


def main():
    """Main function."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    print("Checking compatibility stubs coverage...")
    print("=" * 50)

    # Find stubs
    stubs_status = find_stubs(project_root)

    # Check stub imports
    imports_status = check_stub_imports(project_root, stubs_status)

    # Print results
    print("\nStubs Status:")
    print("-" * 50)
    for path, exists in stubs_status.items():
        status = "✅ Exists" if exists else "❌ Missing"
        print(f"{status} | {path} -> {MOVED_MODULES[path]}")

    print("\nImports Status:")
    print("-" * 50)
    for path, correct in imports_status.items():
        status = "✅ Correct" if correct else "❌ Incorrect"
        print(f"{status} | {path} imports from {MOVED_MODULES[path]}")

    # Summary
    total_modules = len(MOVED_MODULES)
    existing_stubs = sum(1 for exists in stubs_status.values() if exists)
    correct_imports = sum(1 for correct in imports_status.values() if correct)

    print("\nSummary:")
    print("-" * 50)
    print(f"Total modules moved: {total_modules}")
    print(
        f"Existing stubs: {existing_stubs}/{total_modules} ({existing_stubs / total_modules * 100:.1f}%)"
    )
    print(
        f"Correct imports: {correct_imports}/{existing_stubs} ({correct_imports / existing_stubs * 100 if existing_stubs else 0:.1f}%)"
    )

    # Overall result
    if existing_stubs == total_modules and correct_imports == existing_stubs:
        print("\n✅ All modules have correct compatibility stubs")
    else:
        print(
            "\n❌ Some modules are missing compatibility stubs or have incorrect imports"
        )

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
