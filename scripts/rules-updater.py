#!/usr/bin/env python3
"""
PepperPy Rules Updater

This script helps maintain and update Cursor rules for the PepperPy framework.
It provides capabilities for scanning the codebase, validating rules,
generating new rules, and updating rule metadata.

Usage:
    python scripts/rules-updater.py [command]

Commands:
    scan        - Scan codebase and update module maps
    validate    - Validate all rules for syntax and completeness
    generate    - Generate new rules from templates
    version     - Update version numbers and timestamps
    analyze-api - Analyze APIs and update documentation
    help        - Show this help message
"""

import argparse
import datetime
import glob
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# Constants
RULES_DIR = Path(".cursor/rules")
AUTO_GENERATED_DIR = RULES_DIR / "auto-generated"
PEPPERPY_DIR = Path("pepperpy")

# Ensure auto-generated directory exists
AUTO_GENERATED_DIR.mkdir(exist_ok=True, parents=True)


def parse_rule_metadata(content: str) -> Dict[str, str]:
    """Parse metadata from a rule file."""
    metadata = {}

    # Extract metadata from HTML comment at the top of the file
    metadata_match = re.search(r"<!--\s*(.*?)\s*-->", content, re.DOTALL)
    if metadata_match:
        metadata_text = metadata_match.group(1)

        # Extract individual metadata items
        for line in metadata_text.strip().split("\n"):
            line = line.strip()
            if line and line.startswith("@"):
                key_value = line.split(":", 1)
                if len(key_value) == 2:
                    key = key_value[0].strip("@ ").lower()
                    value = key_value[1].strip()
                    metadata[key] = value

    return metadata


def validate_rule(file_path: Path) -> List[str]:
    """Validate a rule file and return a list of issues."""
    issues = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for metadata
        metadata = parse_rule_metadata(content)
        required_metadata = ["title", "description", "glob", "priority"]

        for field in required_metadata:
            if field not in metadata:
                issues.append(f"Missing required metadata: @{field}")

        # Check for main title
        if not re.search(r"^# [^\n]+$", content, re.MULTILINE):
            issues.append("Missing main title (# Title)")

        # Check for overview section
        if not re.search(r"^## Overview", content, re.MULTILINE):
            issues.append("Missing Overview section (## Overview)")

        # Check for conclusion section
        if not re.search(r"^## Conclusion", content, re.MULTILINE):
            issues.append("Missing Conclusion section (## Conclusion)")

    except Exception as e:
        issues.append(f"Error reading file: {str(e)}")

    return issues


def validate_rules() -> Dict[str, List[str]]:
    """Validate all rule files and return issues by file."""
    issues_by_file = {}

    for file_path in glob.glob(str(RULES_DIR / "**" / "*.mdc"), recursive=True):
        path = Path(file_path)
        file_issues = validate_rule(path)

        if file_issues:
            issues_by_file[str(path)] = file_issues

    return issues_by_file


def scan_module(module_path: Path) -> Dict[str, Any]:
    """Scan a Python module for structure information."""
    result = {
        "path": str(module_path),
        "is_package": os.path.isdir(module_path),
        "submodules": [],
        "files": [],
    }

    if not result["is_package"]:
        return result

    # Check if it's a valid Python package
    if not (module_path / "__init__.py").exists():
        return result

    # Scan for submodules and files
    for item in os.listdir(module_path):
        item_path = module_path / item

        # Skip hidden files and directories
        if item.startswith(".") or item.startswith("__pycache__"):
            continue

        if item_path.is_dir() and (item_path / "__init__.py").exists():
            # Recursively scan submodule
            submodule = scan_module(item_path)
            if submodule:
                result["submodules"].append(submodule)
        elif item.endswith(".py"):
            # Add Python file
            result["files"].append({
                "name": item,
                "path": str(item_path),
            })

    # Sort submodules and files alphabetically
    result["submodules"].sort(key=lambda x: x["path"])
    result["files"].sort(key=lambda x: x["name"])

    return result


def scan_codebase() -> Dict[str, Any]:
    """Scan the codebase and return structure information."""
    result = {
        "timestamp": datetime.datetime.now().isoformat(),
        "modules": [],
    }

    if not PEPPERPY_DIR.exists():
        print(f"Error: Main package directory not found: {PEPPERPY_DIR}")
        return result

    # Scan main package
    main_module = scan_module(PEPPERPY_DIR)
    if main_module:
        result["modules"].append(main_module)

    return result


def generate_module_map(scan_result: Dict[str, Any]) -> str:
    """Generate a module map rule from scan results."""
    content = []

    # Add header
    content.append(f"""<!--
@title: PepperPy Module Map
@description: Auto-generated map of modules and structure in the PepperPy framework
@glob: **/*.py
@priority: 600
@version: 1.0
@last_updated: {datetime.datetime.now().strftime("%Y-%m-%d")}
-->

# PepperPy Module Map

## Overview

This is an auto-generated map of the PepperPy framework's module structure.
Last updated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Module Structure
""")

    # Generate module tree
    def format_module_tree(module, indent=0):
        result = []

        # Module/package name
        if module["is_package"]:
            name = os.path.basename(module["path"])
            result.append(f"{'  ' * indent}- **{name}/** - Package")

            # Files
            for file in module["files"]:
                file_name = file["name"]
                result.append(f"{'  ' * (indent + 1)}- {file_name}")

            # Submodules (recursive)
            for submodule in module["submodules"]:
                result.extend(format_module_tree(submodule, indent + 1))

        return result

    # Add module tree for each top-level module
    for module in scan_result["modules"]:
        content.extend(format_module_tree(module))

    # Add module purpose descriptions
    content.append("""
## Module Purposes

Here are brief descriptions of the main modules:

- **pepperpy**: Main package for the PepperPy framework
  - **core/**: Core framework components and base classes
  - **llm/**: Language model integration
  - **rag/**: Retrieval Augmented Generation system
  - **workflow/**: Workflow engine and orchestration
  - **storage/**: Storage and persistence capabilities
  - **hub/**: PepperHub integration
  - **agents/**: Agent framework and implementations
  - **cache/**: Caching system
  - **cli/**: Command-line interface
  - **utils/**: Utility functions and helpers
""")

    # Add conclusion
    content.append("""
## Conclusion

This module map provides an overview of the PepperPy framework's structure.
When adding new code, please follow the established patterns and place files
in the appropriate modules. Refer to the architecture and file management
rules for more detailed guidelines.
""")

    return "\n".join(content)


def update_rule_metadata(file_path: Path) -> bool:
    """Update version and timestamp metadata in a rule file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse existing metadata
        metadata = parse_rule_metadata(content)

        # Update version if present
        if "version" in metadata:
            # Parse version (assume semantic versioning)
            version_parts = metadata["version"].split(".")
            if len(version_parts) >= 3:
                # Increment patch version
                patch = int(version_parts[2])
                version_parts[2] = str(patch + 1)
                new_version = ".".join(version_parts)

                # Replace version in content
                content = re.sub(
                    r"@version:\s*[^\n]+", f"@version: {new_version}", content
                )

        # Update timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        if "last_updated" in metadata:
            # Replace existing timestamp
            content = re.sub(
                r"@last_updated:\s*[^\n]+", f"@last_updated: {timestamp}", content
            )
        else:
            # Add timestamp after priority
            if "priority" in metadata:
                content = re.sub(
                    r"(@priority:[^\n]+)", f"\\1\n@last_updated: {timestamp}", content
                )

        # Write updated content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"Error updating metadata in {file_path}: {str(e)}")
        return False


def generate_rule_from_template(name: str, category: int) -> bool:
    """Generate a new rule file from a template."""
    # Determine file path
    if not name:
        print("Error: Rule name is required")
        return False

    # Convert name to kebab case for filename
    filename = name.lower().replace(" ", "-")
    number = category if 0 <= category < 1000 else 100

    file_path = RULES_DIR / f"{number:03d}-{filename}.mdc"

    if file_path.exists():
        print(f"Error: Rule file already exists: {file_path}")
        return False

    # Format rule title
    title = " ".join(word.capitalize() for word in name.split())

    # Create rule content
    content = f"""<!--
@title: PepperPy {title}
@description: Guidelines for {name.lower()} in the PepperPy framework
@glob: **/*.py
@priority: {number}
@version: 1.0
@last_updated: {datetime.datetime.now().strftime("%Y-%m-%d")}
-->

# PepperPy {title}

## Overview

This rule provides guidelines for {name.lower()} in the PepperPy framework.

## Key Principles

1. **Principle 1**: Description
2. **Principle 2**: Description
3. **Principle 3**: Description

## Implementation Patterns

Example implementation:

```python
# Example code
```

## Best Practices

1. Best practice 1
2. Best practice 2
3. Best practice 3

## Conclusion

Following these guidelines ensures consistent and effective {name.lower()} in the PepperPy framework.
"""

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Generated new rule: {file_path}")
        return True
    except Exception as e:
        print(f"Error generating rule: {str(e)}")
        return False


def analyze_api() -> Dict[str, Any]:
    """Analyze the public API and return information."""
    # This is a simplified version that would need to be expanded
    # with actual code analysis using ast or similar

    result = {
        "timestamp": datetime.datetime.now().isoformat(),
        "modules": {},
    }

    # Find all __init__.py files
    for init_file in glob.glob(
        str(PEPPERPY_DIR / "**" / "__init__.py"), recursive=True
    ):
        module_path = os.path.dirname(init_file)
        module_name = module_path.replace(str(PEPPERPY_DIR), "pepperpy").replace(
            "/", "."
        )

        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for __all__ definitions
        all_match = re.search(r"__all__\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if all_match:
            exports = []
            for item in all_match.group(1).split(","):
                item = item.strip().strip("\"'")
                if item:
                    exports.append(item)

            result["modules"][module_name] = {
                "exports": exports,
                "path": module_path,
            }

    return result


def generate_api_docs(api_info: Dict[str, Any]) -> str:
    """Generate API documentation rule from API analysis."""
    content = []

    # Add header
    content.append(f"""<!--
@title: PepperPy API Documentation
@description: Auto-generated documentation of PepperPy's public API
@glob: **/*.py
@priority: 601
@version: 1.0
@last_updated: {datetime.datetime.now().strftime("%Y-%m-%d")}
-->

# PepperPy API Documentation

## Overview

This is an auto-generated documentation of the PepperPy framework's public API.
Last updated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Public APIs
""")

    # Add module exports
    for module_name, module_info in sorted(api_info["modules"].items()):
        if not module_info.get("exports"):
            continue

        content.append(f"\n### {module_name}")
        content.append("\nExports:")
        content.append("```python")
        for export in sorted(module_info["exports"]):
            content.append(f"from {module_name} import {export}")
        content.append("```")

    # Add conclusion
    content.append("""
## Usage Guidelines

When importing from PepperPy:

1. Always import from the highest-level public API when possible
2. Avoid importing from internal modules
3. Use explicit imports rather than wildcard imports

```python
# Good
from pepperpy.rag import RAGProvider, Document

# Avoid
from pepperpy.rag.providers.basic import BasicRAGProvider  # Internal module
from pepperpy.rag import *  # Wildcard import
```

## Conclusion

This documentation provides an overview of PepperPy's public API.
When developing with PepperPy, use these documented APIs for maximum
compatibility and maintainability.
""")

    return "\n".join(content)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="PepperPy Rules Updater")
    parser.add_argument(
        "command",
        choices=["scan", "validate", "generate", "version", "analyze-api", "help"],
        help="Command to execute",
    )
    parser.add_argument("--name", help="Rule name for generate command")
    parser.add_argument(
        "--category",
        type=int,
        default=100,
        help="Rule category number (0-999) for generate command",
    )

    args = parser.parse_args()

    if args.command == "help":
        print(__doc__)
        return 0

    # Create auto-generated directory if it doesn't exist
    if not AUTO_GENERATED_DIR.exists():
        AUTO_GENERATED_DIR.mkdir(parents=True)

    if args.command == "scan":
        print("Scanning codebase...")
        scan_result = scan_codebase()

        module_map = generate_module_map(scan_result)

        module_map_file = AUTO_GENERATED_DIR / "module-map.mdc"
        with open(module_map_file, "w", encoding="utf-8") as f:
            f.write(module_map)

        print(f"Generated module map: {module_map_file}")

    elif args.command == "validate":
        print("Validating rules...")
        issues = validate_rules()

        if issues:
            print("\nIssues found:")
            for file, file_issues in issues.items():
                print(f"\n{file}:")
                for issue in file_issues:
                    print(f"  - {issue}")

            print(f"\nTotal files with issues: {len(issues)}")
            return 1
        else:
            print("All rules are valid!")

    elif args.command == "generate":
        if not args.name:
            print("Error: --name is required for generate command")
            return 1

        success = generate_rule_from_template(args.name, args.category)
        return 0 if success else 1

    elif args.command == "version":
        print("Updating rule versions and timestamps...")

        updated = 0
        for file_path in glob.glob(str(RULES_DIR / "**" / "*.mdc"), recursive=True):
            if update_rule_metadata(Path(file_path)):
                updated += 1

        print(f"Updated {updated} rule files")

    elif args.command == "analyze-api":
        print("Analyzing PepperPy API...")
        api_info = analyze_api()

        api_docs = generate_api_docs(api_info)

        api_docs_file = AUTO_GENERATED_DIR / "api-docs.mdc"
        with open(api_docs_file, "w", encoding="utf-8") as f:
            f.write(api_docs)

        print(f"Generated API documentation: {api_docs_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
