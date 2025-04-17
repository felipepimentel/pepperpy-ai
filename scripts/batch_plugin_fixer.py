#!/usr/bin/env python3
"""
Plugin Fixer for PepperPy.

This script performs automatic fixes for common issues in plugins.
"""

import argparse
import logging
import os
import sys

import yaml

# Import the validator to reuse validation logic
from plugin_validator import PluginValidationResult, PluginValidator


class PluginFixer:
    """Fixes common issues in PepperPy plugins."""

    def __init__(self, plugins_dir: str = "plugins", dry_run: bool = True) -> None:
        """Initialize fixer.

        Args:
            plugins_dir: Base directory for plugins
            dry_run: Only show changes without applying them
        """
        self.plugins_dir = plugins_dir
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        self.validator = PluginValidator(plugins_dir=plugins_dir)

    def find_plugins_with_issues(self) -> list[tuple[str, PluginValidationResult]]:
        """Find all plugins with validation issues.

        Returns:
            List of tuples with plugin path and validation result
        """
        validation_results = self.validator.validate_all_plugins()
        return [
            (result.plugin_path, result)
            for result in validation_results
            if result.issues
        ]

    def fix_plugin_yaml(
        self, plugin_path: str, validation_result: PluginValidationResult
    ) -> bool:
        """Fix issues in plugin.yaml file.

        Args:
            plugin_path: Path to plugin directory
            validation_result: Validation result with issues

        Returns:
            True if changes were made
        """
        yaml_path = os.path.join(plugin_path, "plugin.yaml")
        if not os.path.exists(yaml_path):
            self.logger.warning(f"Cannot fix missing plugin.yaml: {yaml_path}")
            return False

        changed = False

        try:
            # Read current content
            with open(yaml_path) as f:
                plugin_data = yaml.safe_load(f) or {}

            # Create backup of original data
            original_data = plugin_data.copy()

            # Fix required fields
            for field in self.validator.REQUIRED_YAML_FIELDS:
                if field not in plugin_data or not plugin_data[field]:
                    if field == "name":
                        # Try to generate from directory structure
                        parts = plugin_path.split(os.path.sep)
                        if len(parts) >= 3:
                            # Take the last three parts of the path
                            domain = parts[-3] if parts[-3] != "plugins" else ""
                            category = parts[-2]
                            provider = parts[-1]

                            if domain and category and provider:
                                plugin_data["name"] = f"{domain}/{category}/{provider}"
                                changed = True
                            elif category and provider:
                                plugin_data["name"] = f"{category}/{provider}"
                                changed = True

                    elif field == "version":
                        plugin_data["version"] = "0.1.0"
                        changed = True

                    elif field == "description":
                        # Generate based on name
                        if "name" in plugin_data:
                            parts = plugin_data["name"].split("/")
                            if len(parts) >= 2:
                                provider = parts[-1].replace("_", " ").title()
                                domain = parts[0].replace("_", " ").title()
                                plugin_data["description"] = (
                                    f"{provider} provider for {domain} operations"
                                )
                                changed = True

                    elif field == "author":
                        plugin_data["author"] = "PepperPy Team"
                        changed = True

                    elif field == "plugin_type":
                        # Try to derive from directory structure or name
                        parts = plugin_path.split(os.path.sep)
                        if len(parts) >= 3 and parts[-3] != "plugins":
                            plugin_data["plugin_type"] = parts[-3]
                            changed = True
                        elif "name" in plugin_data:
                            name_parts = plugin_data["name"].split("/")
                            if len(name_parts) >= 2:
                                plugin_data["plugin_type"] = name_parts[0]
                                changed = True

                    elif field == "category":
                        # Try to derive from directory structure or name
                        parts = plugin_path.split(os.path.sep)
                        if len(parts) >= 2:
                            plugin_data["category"] = parts[-2]
                            changed = True
                        elif "name" in plugin_data:
                            name_parts = plugin_data["name"].split("/")
                            if len(name_parts) >= 2:
                                plugin_data["category"] = (
                                    name_parts[1]
                                    if len(name_parts) >= 3
                                    else "provider"
                                )
                                changed = True

                    elif field == "provider_name":
                        # Try to derive from directory structure or name
                        parts = plugin_path.split(os.path.sep)
                        if len(parts) >= 1:
                            plugin_data["provider_name"] = parts[-1]
                            changed = True
                        elif "name" in plugin_data:
                            name_parts = plugin_data["name"].split("/")
                            if len(name_parts) >= 1:
                                plugin_data["provider_name"] = name_parts[-1]
                                changed = True

                    elif field == "entry_point":
                        # Try to generate from provider name
                        if "provider_name" in plugin_data:
                            provider_name = plugin_data["provider_name"]
                            class_name = (
                                "".join(
                                    word.title() for word in provider_name.split("_")
                                )
                                + "Provider"
                            )
                            plugin_data["entry_point"] = f"provider.{class_name}"
                            changed = True

            # Fix config schema if missing
            if "config_schema" not in plugin_data:
                plugin_data["config_schema"] = {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                }
                changed = True

            # Fix default config if missing
            if "default_config" not in plugin_data:
                plugin_data["default_config"] = {}
                changed = True

            # Fix examples if missing
            if "examples" not in plugin_data:
                plugin_data["examples"] = [
                    {
                        "name": "basic_example",
                        "description": "Basic usage example",
                        "input": {"task": "default_task"},
                        "expected_output": {"status": "success"},
                    }
                ]
                changed = True

            # Write changes if needed
            if changed:
                if self.dry_run:
                    self.logger.info(f"Would fix plugin.yaml at {yaml_path} (dry run)")
                    # Show diff
                    for key in set(
                        list(original_data.keys()) + list(plugin_data.keys())
                    ):
                        if key not in original_data:
                            self.logger.info(f"  + {key}: {plugin_data[key]}")
                        elif key not in plugin_data:
                            self.logger.info(f"  - {key}: {original_data[key]}")
                        elif original_data[key] != plugin_data[key]:
                            self.logger.info(
                                f"  ~ {key}: {original_data[key]} -> {plugin_data[key]}"
                            )
                else:
                    self.logger.info(f"Fixing plugin.yaml at {yaml_path}")
                    with open(yaml_path, "w") as f:
                        yaml.dump(
                            plugin_data, f, default_flow_style=False, sort_keys=False
                        )

        except Exception as e:
            self.logger.error(f"Error fixing plugin.yaml at {yaml_path}: {e}")
            return False

        return changed

    def create_init_file(self, plugin_path: str) -> bool:
        """Create or fix __init__.py file.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            True if changes were made
        """
        init_path = os.path.join(plugin_path, "__init__.py")
        provider_path = os.path.join(plugin_path, "provider.py")
        yaml_path = os.path.join(plugin_path, "plugin.yaml")

        if not os.path.exists(provider_path) or not os.path.exists(yaml_path):
            self.logger.warning(
                f"Cannot create __init__.py without provider.py and plugin.yaml: {plugin_path}"
            )
            return False

        try:
            # Load plugin.yaml to get provider name
            with open(yaml_path) as f:
                plugin_data = yaml.safe_load(f) or {}

            entry_point = plugin_data.get("entry_point", "")
            if not entry_point or "." not in entry_point:
                self.logger.warning(
                    f"Invalid entry_point in plugin.yaml: {entry_point}"
                )
                return False

            # Extract class name from entry point
            module_name, class_name = entry_point.split(".", 1)

            # Create content
            content = f'''"""
Plugin for {plugin_data.get("name", "domain provider")}.

This plugin provides {plugin_data.get("description", "domain-specific capabilities")}.
"""

from .provider import {class_name}

__all__ = ["{class_name}"]
'''

            if not os.path.exists(init_path) or open(init_path).read() != content:
                if self.dry_run:
                    self.logger.info(
                        f"Would create/update __init__.py at {init_path} (dry run)"
                    )
                    if os.path.exists(init_path):
                        self.logger.info(f"Current content:\n{open(init_path).read()}")
                    self.logger.info(f"New content:\n{content}")
                else:
                    self.logger.info(f"Creating/updating __init__.py at {init_path}")
                    with open(init_path, "w") as f:
                        f.write(content)
                return True

        except Exception as e:
            self.logger.error(f"Error creating __init__.py at {init_path}: {e}")

        return False

    def create_requirements_file(self, plugin_path: str) -> bool:
        """Create requirements.txt file if missing.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            True if changes were made
        """
        req_path = os.path.join(plugin_path, "requirements.txt")

        if os.path.exists(req_path):
            return False

        content = (
            "# Plugin dependencies\n# Add specific dependencies and versions here\n"
        )

        if self.dry_run:
            self.logger.info(f"Would create requirements.txt at {req_path} (dry run)")
            self.logger.info(f"Content:\n{content}")
        else:
            self.logger.info(f"Creating requirements.txt at {req_path}")
            with open(req_path, "w") as f:
                f.write(content)

        return True

    def fix_plugin(
        self, plugin_path: str, validation_result: PluginValidationResult
    ) -> int:
        """Fix issues in a plugin.

        Args:
            plugin_path: Path to plugin directory
            validation_result: Validation result with issues

        Returns:
            Number of fixes applied
        """
        fixes_count = 0

        # Fix plugin.yaml
        if self.fix_plugin_yaml(plugin_path, validation_result):
            fixes_count += 1

        # Create/fix __init__.py
        if self.create_init_file(plugin_path):
            fixes_count += 1

        # Create requirements.txt if missing
        if self.create_requirements_file(plugin_path):
            fixes_count += 1

        return fixes_count

    def fix_all_plugins(self) -> dict[str, int]:
        """Fix issues in all plugins.

        Returns:
            Dictionary mapping plugin paths to number of fixes applied
        """
        plugins_with_issues = self.find_plugins_with_issues()
        fixes_by_plugin = {}

        for plugin_path, validation_result in plugins_with_issues:
            fixes_count = self.fix_plugin(plugin_path, validation_result)
            fixes_by_plugin[plugin_path] = fixes_count

        return fixes_by_plugin


def setup_logging(verbose: bool) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    """Run the fixer.

    Returns:
        Exit code (0 for success, non-zero otherwise)
    """
    parser = argparse.ArgumentParser(
        description="Fix common issues in PepperPy plugins"
    )
    parser.add_argument(
        "-d", "--plugins-dir", default="plugins", help="Base plugins directory"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only show changes without applying them"
    )
    parser.add_argument("-s", "--single", help="Fix a single plugin directory")
    args = parser.parse_args()

    setup_logging(args.verbose)

    fixer = PluginFixer(plugins_dir=args.plugins_dir, dry_run=args.dry_run)

    if args.single:
        # Fix a single plugin
        plugin_path = args.single
        if not os.path.isdir(plugin_path):
            print(f"Error: {plugin_path} is not a directory")
            return 1

        validator = PluginValidator(plugins_dir=args.plugins_dir)
        validation_result = validator.validate_plugin(plugin_path)

        fixes_count = fixer.fix_plugin(plugin_path, validation_result)

        print(f"Applied {fixes_count} fixes to {plugin_path}")

        # Validate again to check if issues were resolved
        if not args.dry_run:
            new_validation = validator.validate_plugin(plugin_path)
            if new_validation.issues:
                print(f"Remaining issues ({len(new_validation.issues)}):")
                print(new_validation)
            else:
                print("All issues resolved!")

    else:
        # Fix all plugins with issues
        fixes_by_plugin = fixer.fix_all_plugins()

        total_plugins = len(fixes_by_plugin)
        total_fixes = sum(fixes_by_plugin.values())

        print(f"Applied {total_fixes} fixes to {total_plugins} plugins")

        # Show detailed report
        for plugin_path, fixes_count in fixes_by_plugin.items():
            if fixes_count > 0:
                print(f"  {plugin_path}: {fixes_count} fixes")

        # Validate again to check if issues were resolved
        if not args.dry_run and total_fixes > 0:
            validator = PluginValidator(plugins_dir=args.plugins_dir)
            results = validator.validate_all_plugins()

            plugins_with_issues = [r for r in results if r.issues]
            if plugins_with_issues:
                print(f"\nRemaining issues in {len(plugins_with_issues)} plugins:")
                for result in plugins_with_issues:
                    print(f"  {result.plugin_path}: {len(result.issues)} issues")
            else:
                print("\nAll issues resolved!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
