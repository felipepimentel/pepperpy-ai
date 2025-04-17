#!/usr/bin/env python3
"""
Batch fix PepperPy plugins.

This script fixes multiple plugins at once by generating properly formatted
templates for each plugin.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def read_fix_list(fix_list_file: Path) -> dict[str, set[str]]:
    """Read the fix list file and extract plugins by category.

    Args:
        fix_list_file: Path to the fix list file

    Returns:
        Dictionary of categories to sets of plugin paths
    """
    plugins_by_category = {}
    current_category = None

    with open(fix_list_file) as f:
        for line in f:
            line = line.strip()

            # Check for category headers
            if line.startswith("### "):
                current_category = line[4:].strip()
                plugins_by_category[current_category] = set()

            # Check for plugin paths (marked with backticks)
            elif line.startswith("- `") and line.endswith("`") and current_category:
                plugin_path = line[3:-1].strip()
                plugins_by_category[current_category].add(plugin_path)

    return plugins_by_category


def generate_plugin_template(plugin_path: Path) -> bool:
    """Generate a template for a plugin.

    Args:
        plugin_path: Path to the plugin.yaml file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Run the template generator script
        cmd = [
            "python",
            "scripts/generate_plugin_template.py",
            "--plugin",
            str(plugin_path),
            "--output-dir",
            str(plugin_path.parent),
        ]

        # Run the command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            print(f"Error generating template for {plugin_path}: {result.stderr}")
            return False

        return True

    except Exception as e:
        print(f"Error generating template for {plugin_path}: {e}")
        return False


def validate_plugin(plugin_path: Path) -> bool:
    """Validate a plugin.

    Args:
        plugin_path: Path to the plugin.yaml file

    Returns:
        True if valid, False otherwise
    """
    try:
        # Run the validation script
        cmd = ["python", "scripts/validate_plugins.py", "--plugin", str(plugin_path)]

        # Run the command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        # Check if plugin is valid (return code 0)
        return result.returncode == 0

    except Exception as e:
        print(f"Error validating {plugin_path}: {e}")
        return False


def fix_plugins_by_category(
    category: str,
    plugins: set[str],
    specific_plugin: str | None = None,
    validate: bool = True,
    dry_run: bool = False,
) -> dict[str, list[str]]:
    """Fix plugins in a category.

    Args:
        category: Category name
        plugins: Set of plugin paths
        specific_plugin: If set, only fix this specific plugin
        validate: Whether to validate plugins after fixing
        dry_run: Whether to only print what would be done

    Returns:
        Dictionary of status to lists of plugin paths
    """
    results = {"fixed": [], "failed": [], "skipped": []}

    print(f"Processing {len(plugins)} plugins in category '{category}'...")

    # If specific plugin is provided, filter the set
    if specific_plugin:
        filtered_plugins = {p for p in plugins if specific_plugin in p}
        if not filtered_plugins:
            print(
                f"  Warning: Plugin {specific_plugin} not found in category '{category}'"
            )
            return results
        plugins = filtered_plugins
        print(f"  Filtered to {len(plugins)} plugins matching '{specific_plugin}'")

    for plugin_path_str in sorted(plugins):
        plugin_path = Path(plugin_path_str)

        if not plugin_path.exists():
            print(f"  Skipping {plugin_path} (not found)")
            results["skipped"].append(str(plugin_path))
            continue

        print(f"  Processing {plugin_path}...")

        if dry_run:
            print(f"    Would fix {plugin_path}")
            results["skipped"].append(str(plugin_path))
            continue

        # Generate template
        success = generate_plugin_template(plugin_path)

        if not success:
            print(f"    Failed to fix {plugin_path}")
            results["failed"].append(str(plugin_path))
            continue

        # Validate if requested
        if validate:
            valid = validate_plugin(plugin_path)

            if valid:
                print(f"    Successfully fixed {plugin_path}")
                results["fixed"].append(str(plugin_path))
            else:
                print(f"    Failed validation for {plugin_path}")
                results["failed"].append(str(plugin_path))
        else:
            print(f"    Fixed {plugin_path} (not validated)")
            results["fixed"].append(str(plugin_path))

    return results


def main() -> int:
    """Run the plugin fixer."""
    parser = argparse.ArgumentParser(description="Batch fix PepperPy plugins")
    parser.add_argument(
        "--fix-list",
        type=str,
        help="Path to file with list of plugins to fix",
        required=False,
    )
    parser.add_argument(
        "--plugin",
        type=str,
        help="Individual plugin to fix",
        required=False,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation after fixing",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Only fix plugins in this category",
        required=False,
    )

    args = parser.parse_args()

    # Check required arguments
    if not args.fix_list and not args.plugin:
        parser.error("Either --fix-list or --plugin is required")

    if args.plugin:
        plugin_path = Path(args.plugin)
        if not plugin_path.exists():
            print(f"Plugin file not found: {plugin_path}")
            return 1

        print(f"Processing single plugin: {plugin_path}")

        if args.dry_run:
            print(f"Would fix {plugin_path}")
            return 0

        success = generate_plugin_template(plugin_path)

        if not success:
            print(f"Failed to fix {plugin_path}")
            return 1

        if not args.no_validate:
            valid = validate_plugin(plugin_path)
            if valid:
                print(f"Successfully fixed and validated {plugin_path}")
            else:
                print(f"Fixed but failed validation for {plugin_path}")
                return 1
        else:
            print(f"Fixed {plugin_path} (not validated)")

        return 0

    # Process multiple plugins from fix list
    fix_list_path = Path(args.fix_list)
    if not fix_list_path.exists():
        print(f"Fix list file not found: {fix_list_path}")
        return 1

    # Read plugins by category
    plugins_by_category = read_fix_list(fix_list_path)
    print(
        f"Found {sum(len(p) for p in plugins_by_category.values())} plugins in {len(plugins_by_category)} categories"
    )

    # Process each category
    all_results = {
        "fixed": [],
        "failed": [],
        "skipped": [],
    }

    for category, plugins in plugins_by_category.items():
        # Skip category if specified and doesn't match
        if args.category and category != args.category:
            continue

        # Fix plugins in this category
        results = fix_plugins_by_category(
            category=category,
            plugins=plugins,
            validate=not args.no_validate,
            dry_run=args.dry_run,
        )

        # Merge results
        for status, paths in results.items():
            all_results[status].extend(paths)

    # Print summary
    print("\nSummary:")
    print(f"  Fixed: {len(all_results['fixed'])}")
    print(f"  Failed: {len(all_results['failed'])}")
    print(f"  Skipped: {len(all_results['skipped'])}")

    # Return success if no failures
    return 0 if not all_results["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
