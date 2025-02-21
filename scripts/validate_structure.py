#!/usr/bin/env python3
"""Project structure validation script.

This script validates the project structure against the specification, checking:
- Required directories exist
- Required files exist
- File naming conventions
- Directory organization
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent

# Required project structure
REQUIRED_STRUCTURE = {
    "pepperpy": {
        "core": {
            "errors.py": None,
            "extensions.py": None,
            "layers.py": None,
            "types.py": None,
        },
        "agents": {
            "base.py": None,
            "config.py": None,
            "factory.py": None,
        },
        "workflows": {
            "base.py": None,
            "config.py": None,
            "steps.py": None,
        },
        "providers": {
            "base.py": None,
            "llm": {
                "base.py": None,
                "openai.py": None,
                "anthropic.py": None,
            },
            "storage": {
                "base.py": None,
                "local.py": None,
                "cloud.py": None,
            },
            "memory": {
                "base.py": None,
                "redis.py": None,
                "postgres.py": None,
            },
        },
        "events": {
            "base.py": None,
            "handlers": {
                "base.py": None,
            },
            "hooks": {
                "base.py": None,
            },
        },
        "content": {
            "base.py": None,
            "synthesis.py": None,
        },
        "hub": {
            "base.py": None,
            "marketplace.py": None,
            "publishing.py": None,
            "security.py": None,
            "storage.py": None,
        },
        "monitoring": {
            "base.py": None,
            "metrics.py": None,
            "tracing.py": None,
        },
        "cli": {
            "base.py": None,
            "commands": {
                "agent.py": None,
                "workflow.py": None,
                "hub.py": None,
                "config.py": None,
            },
        },
    },
    "tests": {
        "unit": {
            "core": {},
            "agents": {},
            "workflows": {},
            "providers": {},
            "events": {},
            "content": {},
            "hub": {},
            "monitoring": {},
            "cli": {},
        },
        "integration": {
            "providers": {},
            "workflows": {},
            "hub": {},
        },
    },
    "docs": {
        "index.md": None,
        "installation.md": None,
        "quickstart.md": None,
        "concepts.md": None,
        "user-guide": {
            "agents.md": None,
            "workflows.md": None,
            "providers.md": None,
            "content.md": None,
            "cli.md": None,
        },
        "api": {
            "core.md": None,
            "agents.md": None,
            "workflows.md": None,
            "providers.md": None,
            "events.md": None,
            "content.md": None,
            "hub.md": None,
            "monitoring.md": None,
            "cli.md": None,
        },
    },
    "scripts": {
        "setup.py": None,
        "check.sh": None,
        "clean.sh": None,
        "validate_structure.py": None,
    },
}

# File naming conventions
NAMING_CONVENTIONS = {
    r"^[a-z][a-z0-9_]*\.py$": "Python files",
    r"^[A-Z][a-zA-Z0-9]*\.md$": "Documentation files",
    r"^[a-z][a-z0-9_]*\.sh$": "Shell scripts",
}


def validate_path_exists(path: Path, required: Dict) -> List[str]:
    """Validate that a path exists and contains required files/directories.

    Args:
        path: Path to validate
        required: Dictionary of required files/directories

    Returns:
        List of validation errors
    """
    errors = []

    # Check path exists
    if not path.exists():
        return [f"Missing path: {path}"]

    # Check required files/directories
    for name, subrequired in required.items():
        subpath = path / name

        # If subrequired is None, it's a file
        if subrequired is None:
            if not subpath.is_file():
                errors.append(f"Missing file: {subpath}")
        # Otherwise it's a directory
        else:
            if not subpath.is_dir():
                errors.append(f"Missing directory: {subpath}")
            else:
                errors.extend(validate_path_exists(subpath, subrequired))

    return errors


def validate_naming_conventions(
    path: Path, seen_files: Optional[Set[Path]] = None
) -> List[str]:
    """Validate file naming conventions recursively.

    Args:
        path: Path to validate
        seen_files: Set of files already validated

    Returns:
        List of validation errors
    """
    import re

    errors = []
    if seen_files is None:
        seen_files = set()

    # Skip if path doesn't exist
    if not path.exists():
        return errors

    # Validate each file/directory
    for item in path.iterdir():
        # Skip if already seen
        if item in seen_files:
            continue
        seen_files.add(item)

        # Skip special directories
        if item.name.startswith("."):
            continue

        # Validate file naming
        if item.is_file():
            valid = False
            for pattern, description in NAMING_CONVENTIONS.items():
                if re.match(pattern, item.name):
                    valid = True
                    break
            if not valid:
                errors.append(f"Invalid {description} name: {item}")

        # Recurse into directories
        elif item.is_dir():
            errors.extend(validate_naming_conventions(item, seen_files))

    return errors


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Validating project structure...")

    # Validate required structure
    structure_errors = validate_path_exists(PROJECT_ROOT, REQUIRED_STRUCTURE)
    if structure_errors:
        print("\nStructure validation errors:")
        for error in structure_errors:
            print(f"  - {error}")

    # Validate naming conventions
    naming_errors = validate_naming_conventions(PROJECT_ROOT)
    if naming_errors:
        print("\nNaming convention errors:")
        for error in naming_errors:
            print(f"  - {error}")

    # Return status
    if structure_errors or naming_errors:
        print("\nValidation failed!")
        return 1
    else:
        print("\nValidation successful!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
