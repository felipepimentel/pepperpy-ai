#!/usr/bin/env python3
"""
Generate a prioritized fix list for PepperPy plugins.

This script reads validation results and generates a prioritized list of
plugins to fix, grouping similar issues together.
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# Issue categories and their priority (lower = higher priority)
CATEGORIES = {
    "inheritance": {
        "pattern": r"(inherits from ProviderPlugin instead of BasePluginProvider|does not inherit from BasePluginProvider)",
        "priority": 1,
        "description": "Incorrect inheritance (should use BasePluginProvider)",
    },
    "hardcoded_attributes": {
        "pattern": r"Hardcoded attribute '([^']+)'",
        "priority": 2,
        "description": "Hardcoded attributes (should use self.config)",
    },
    "initialize_method": {
        "pattern": r"(initialize method .* does not call super\(\)\.initialize\(\)|Missing initialize method)",
        "priority": 3,
        "description": "Missing or incorrect initialize method",
    },
    "cleanup_method": {
        "pattern": r"(cleanup method .* does not call super\(\)\.cleanup\(\)|Missing cleanup method)",
        "priority": 4,
        "description": "Missing or incorrect cleanup method",
    },
    "config_usage": {
        "pattern": r"directly accesses attributes that should use self\.config",
        "priority": 5,
        "description": "Direct attribute access (should use self.config)",
    },
    "yaml_format": {
        "pattern": r"(Invalid plugin name|Missing required field|must be a dictionary)",
        "priority": 6,
        "description": "Invalid plugin.yaml format",
    },
    "examples": {
        "pattern": r"No examples defined",
        "priority": 7,
        "description": "No examples defined in plugin.yaml",
    },
    "parse_error": {
        "pattern": r"Error parsing",
        "priority": 8,
        "description": "Python parsing error (syntax issues)",
    },
}


def extract_issues(results_file: Path) -> dict[str, list[str]]:
    """Extract issues from validation results.

    Args:
        results_file: Path to validation results file

    Returns:
        Dictionary of plugin paths to list of issues
    """
    issues: dict[str, list[str]] = defaultdict(list)
    current_plugin = None

    with open(results_file) as f:
        for line in f:
            line = line.strip()

            # Check if this is a new plugin
            if line.startswith("Validating "):
                current_plugin = line.split("Validating ")[1]

            # Check if this is an issue
            elif line.startswith("ERROR: ") or line.startswith("WARNING: "):
                if current_plugin:
                    issue = line.split(": ", 1)[1]
                    issues[current_plugin].append(issue)

    return issues


def categorize_issues(issues: dict[str, list[str]]) -> dict[str, dict[str, set[str]]]:
    """Categorize issues by type.

    Args:
        issues: Dictionary of plugin paths to list of issues

    Returns:
        Dictionary of issue categories to sets of affected plugins
    """
    categories: dict[str, dict[str, set[str]]] = {}

    for category, info in CATEGORIES.items():
        categories[category] = {
            "priority": info["priority"],
            "description": info["description"],
            "plugins": set(),
        }

    # Categorize each issue
    for plugin, plugin_issues in issues.items():
        for issue in plugin_issues:
            for category, info in CATEGORIES.items():
                if re.search(info["pattern"], issue):
                    categories[category]["plugins"].add(plugin)
                    break

    return categories


def generate_fix_list(
    categories: dict[str, dict[str, set[str]]],
) -> list[tuple[str, str, set[str]]]:
    """Generate a prioritized fix list.

    Args:
        categories: Dictionary of issue categories to sets of affected plugins

    Returns:
        List of (category, description, plugins) tuples, sorted by priority
    """
    fix_list = []

    for category, info in categories.items():
        if info["plugins"]:
            fix_list.append((category, info["description"], info["plugins"]))

    # Sort by priority
    fix_list.sort(key=lambda x: CATEGORIES[x[0]]["priority"])

    return fix_list


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate fix list for PepperPy plugins"
    )
    parser.add_argument("results_file", help="Path to validation results")
    parser.add_argument("--output", "-o", help="Output file")
    args = parser.parse_args()

    results_file = Path(args.results_file)
    if not results_file.exists():
        print(f"Error: Results file '{results_file}' not found")
        return 1

    # Redirect output if needed
    original_stdout = sys.stdout
    if args.output:
        try:
            sys.stdout = open(args.output, "w")
        except Exception as e:
            print(f"Error opening output file: {e}")
            return 1

    try:
        # Extract and categorize issues
        issues = extract_issues(results_file)
        categories = categorize_issues(issues)
        fix_list = generate_fix_list(categories)

        # Print fix list
        print("# PepperPy Plugin Fix List")
        print()
        print("## Summary")
        print()
        print(f"Total plugins with issues: {len(issues)}")
        print()

        for category, description, plugins in fix_list:
            print(f"- **{description}**: {len(plugins)} plugins")

        print()
        print("## Detailed Fix List")
        print()

        for category, description, plugins in fix_list:
            print(f"### {description}")
            print()
            print(f"{len(plugins)} plugins affected:")
            print()

            for plugin in sorted(plugins):
                print(f"- `{plugin}`")

            print()

        return 0

    finally:
        # Restore original stdout if redirected
        if args.output:
            sys.stdout.close()
            sys.stdout = original_stdout


if __name__ == "__main__":
    sys.exit(main())
