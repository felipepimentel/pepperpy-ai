#!/usr/bin/env python3
"""
Batch fix PepperPy plugins.

This script fixes multiple plugins at once by generating properly formatted
templates for each plugin and backing up the originals.
"""

import argparse
import shutil
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


def backup_plugin(plugin_path: Path) -> Path:
    """Create a backup of a plugin directory.

    Args:
        plugin_path: Path to the plugin.yaml file

    Returns:
        Path to backup directory
    """
    plugin_dir = plugin_path.parent
    backup_dir = plugin_dir.with_name(f"{plugin_dir.name}_backup")

    # Remove existing backup if it exists
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    # Create backup
    shutil.copytree(plugin_dir, backup_dir)

    return backup_dir


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
    backup: bool = True,
    validate: bool = True,
    dry_run: bool = False,
) -> dict[str, list[str]]:
    """Fix plugins in a category.

    Args:
        category: Category name
        plugins: Set of plugin paths
        specific_plugin: If set, only fix this specific plugin
        backup: Whether to create backups
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

        # Create backup
        if backup:
            try:
                backup_path = backup_plugin(plugin_path)
                print(f"    Created backup at {backup_path}")
            except Exception as e:
                print(f"    Error creating backup: {e}")
                results["failed"].append(str(plugin_path))
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
                print(f"    Fixed but still has issues: {plugin_path}")
                results["failed"].append(str(plugin_path))
        else:
            print(f"    Fixed {plugin_path} (not validated)")
            results["fixed"].append(str(plugin_path))

    return results


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Batch fix PepperPy plugins")
    parser.add_argument("fix_list", help="Path to the fix list file")
    parser.add_argument("--category", "-c", help="Category to process (default: all)")
    parser.add_argument(
        "--plugin",
        "-p",
        help="Specific plugin to fix (must be part of the chosen category or any category if none specified)",
    )
    parser.add_argument(
        "--no-backup", "-B", action="store_true", help="Don't create backups"
    )
    parser.add_argument(
        "--no-validate", "-V", action="store_true", help="Don't validate after fixing"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Only print what would be done"
    )
    parser.add_argument("--output", "-o", help="Output file for results")
    args = parser.parse_args()

    fix_list_file = Path(args.fix_list)
    if not fix_list_file.exists():
        print(f"Error: Fix list file '{fix_list_file}' not found")
        return 1

    # Redirect output to file if specified
    original_stdout = sys.stdout
    if args.output:
        try:
            sys.stdout = open(args.output, "w")
        except Exception as e:
            print(f"Error opening output file: {e}")
            return 1

    try:
        # Read fix list
        plugins_by_category = read_fix_list(fix_list_file)

        if not plugins_by_category:
            print("No plugins found in fix list")
            return 1

        # Process requested categories
        results = {"fixed": [], "failed": [], "skipped": []}

        # If specific plugin is provided but no category, find which categories contain it
        if args.plugin and not args.category:
            found_categories = []
            for category, plugins in plugins_by_category.items():
                if any(args.plugin in p for p in plugins):
                    found_categories.append(category)

            if not found_categories:
                print(f"Error: Plugin '{args.plugin}' not found in any category")
                return 1

            print(f"Found plugin '{args.plugin}' in {len(found_categories)} categories")

            # Process each matching category
            for category in found_categories:
                category_results = fix_plugins_by_category(
                    category,
                    plugins_by_category[category],
                    specific_plugin=args.plugin,
                    backup=not args.no_backup,
                    validate=not args.no_validate,
                    dry_run=args.dry_run,
                )

                # Merge results
                for status, plugins in category_results.items():
                    results[status].extend(plugins)

        elif args.category:
            if args.category not in plugins_by_category:
                print(f"Error: Category '{args.category}' not found in fix list")
                return 1

            # Process single category
            category_results = fix_plugins_by_category(
                args.category,
                plugins_by_category[args.category],
                specific_plugin=args.plugin,
                backup=not args.no_backup,
                validate=not args.no_validate,
                dry_run=args.dry_run,
            )

            # Merge results
            for status, plugins in category_results.items():
                results[status].extend(plugins)
        else:
            # Process all categories
            for category, plugins in plugins_by_category.items():
                category_results = fix_plugins_by_category(
                    category,
                    plugins,
                    specific_plugin=args.plugin,
                    backup=not args.no_backup,
                    validate=not args.no_validate,
                    dry_run=args.dry_run,
                )

                # Merge results
                for status, plugins in category_results.items():
                    results[status].extend(plugins)

        # Print summary
        print("\nSummary:")
        print(f"  Fixed: {len(results['fixed'])} plugins")
        print(f"  Failed: {len(results['failed'])} plugins")
        print(f"  Skipped: {len(results['skipped'])} plugins")

        return 0 if not results["failed"] else 1

    finally:
        # Restore original stdout if redirected
        if args.output:
            sys.stdout.close()
            sys.stdout = original_stdout


if __name__ == "__main__":
    sys.exit(main())
