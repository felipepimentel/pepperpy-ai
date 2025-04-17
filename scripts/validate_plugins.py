#!/usr/bin/env python3
"""
Plugin Validator for PepperPy.

This script validates all plugins in the PepperPy repository to ensure they
follow the implementation guidelines.
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Any

import yaml

# Constants
PLUGINS_DIR = Path("plugins")
REQUIRED_YAML_FIELDS = [
    "name",
    "version",
    "description",
    "author",
    "plugin_type",
    "category",
    "provider_name",
    "entry_point",
    "config_schema",
    "default_config",
]


class PluginValidator:
    """Validator for PepperPy plugins."""

    def __init__(self, verbose: bool = False, fix: bool = False):
        """Initialize the validator.

        Args:
            verbose: Whether to print verbose output
            fix: Whether to automatically fix issues (not implemented yet)
        """
        self.verbose = verbose
        self.fix = fix
        self.issues: list[str] = []
        self.warnings: list[str] = []
        self.all_plugins: list[dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled.

        Args:
            message: Message to log
        """
        if self.verbose:
            try:
                print(message)
            except BrokenPipeError:
                # Handle broken pipe error (e.g., when piping to head)
                sys.stderr.close()
                return

    def add_issue(self, message: str) -> None:
        """Add an issue to the list of issues.

        Args:
            message: Issue message
        """
        self.issues.append(message)
        self.log(f"ERROR: {message}")

    def add_warning(self, message: str) -> None:
        """Add a warning to the list of warnings.

        Args:
            message: Warning message
        """
        self.warnings.append(message)
        self.log(f"WARNING: {message}")

    def find_plugins(self) -> list[Path]:
        """Find all plugin.yaml files in the plugins directory.

        Returns:
            List of paths to plugin.yaml files
        """
        if not PLUGINS_DIR.exists():
            self.add_issue(f"Plugins directory '{PLUGINS_DIR}' does not exist")
            return []

        plugins = list(PLUGINS_DIR.glob("**/plugin.yaml"))
        self.log(f"Found {len(plugins)} plugins")
        return plugins

    def validate_plugin_yaml(self, plugin_path: Path) -> dict[str, Any] | None:
        """Validate a plugin.yaml file.

        Args:
            plugin_path: Path to the plugin.yaml file

        Returns:
            Plugin data if valid, None otherwise
        """
        try:
            with open(plugin_path) as f:
                plugin_data = yaml.safe_load(f)

            # Basic validation
            for field in REQUIRED_YAML_FIELDS:
                if field not in plugin_data:
                    self.add_issue(f"Missing required field '{field}' in {plugin_path}")
                    return None

            # Check name format
            name = plugin_data.get("name", "")
            if not name or "/" not in name:
                self.add_issue(
                    f"Invalid plugin name '{name}' in {plugin_path}. Expected format: 'domain/provider_name'"
                )

            # Check config_schema
            config_schema = plugin_data.get("config_schema", {})
            if not isinstance(config_schema, dict) or not config_schema.get(
                "properties"
            ):
                self.add_warning(f"config_schema in {plugin_path} has no properties")

            # Check default_config
            default_config = plugin_data.get("default_config", {})
            if not isinstance(default_config, dict):
                self.add_issue(f"default_config in {plugin_path} must be a dictionary")

            # Check entry_point
            entry_point = plugin_data.get("entry_point", "")
            if not entry_point:
                self.add_issue(f"Missing entry_point in {plugin_path}")
            elif "." not in entry_point:
                self.add_issue(
                    f"Invalid entry_point '{entry_point}' in {plugin_path}. Expected format: 'module.ClassName'"
                )

            # Check examples
            examples = plugin_data.get("examples", [])
            if not examples:
                self.add_warning(f"No examples defined in {plugin_path}")

            return plugin_data
        except Exception as e:
            self.add_issue(f"Error parsing {plugin_path}: {e}")
            return None

    def parse_python_file(self, file_path: Path) -> ast.Module | None:
        """Parse a Python file to AST.

        Args:
            file_path: Path to the Python file

        Returns:
            AST module if parsing was successful, None otherwise
        """
        try:
            with open(file_path) as f:
                return ast.parse(f.read(), filename=str(file_path))
        except Exception as e:
            self.add_issue(f"Error parsing {file_path}: {e}")
            return None

    def find_provider_class(
        self, module_ast: ast.Module, class_name: str
    ) -> ast.ClassDef | None:
        """Find a provider class in an AST module.

        Args:
            module_ast: AST module to search
            class_name: Name of the class to find

        Returns:
            AST ClassDef if found, None otherwise
        """
        for node in module_ast.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def check_inheritance(self, class_def: ast.ClassDef, plugin_path: Path) -> bool:
        """Check if a class inherits from BasePluginProvider.

        Args:
            class_def: AST ClassDef to check
            plugin_path: Path to the plugin.yaml file

        Returns:
            True if inheritance is correct, False otherwise
        """
        # Check for direct inheritance from BasePluginProvider
        has_base_plugin_provider = False
        has_provider_plugin = False

        for base in class_def.bases:
            if isinstance(base, ast.Name):
                if base.id == "BasePluginProvider":
                    has_base_plugin_provider = True
                elif base.id == "ProviderPlugin":
                    has_provider_plugin = True

            elif isinstance(base, ast.Attribute):
                if (
                    isinstance(base.value, ast.Name)
                    and base.attr == "BasePluginProvider"
                ):
                    has_base_plugin_provider = True
                elif isinstance(base.value, ast.Name) and base.attr == "ProviderPlugin":
                    has_provider_plugin = True

        if not has_base_plugin_provider:
            if has_provider_plugin:
                self.add_issue(
                    f"Class {class_def.name} in {plugin_path.parent} inherits from ProviderPlugin instead of BasePluginProvider"
                )
            else:
                self.add_issue(
                    f"Class {class_def.name} in {plugin_path.parent} does not inherit from BasePluginProvider"
                )
            return False

        return True

    def check_hardcoded_attributes(
        self, class_def: ast.ClassDef, plugin_path: Path
    ) -> bool:
        """Check if a class has hardcoded attributes.

        Args:
            class_def: AST ClassDef to check
            plugin_path: Path to the plugin.yaml file

        Returns:
            True if no hardcoded attributes found, False otherwise
        """
        # Look for class-level attribute assignments that might be hardcoded config
        has_hardcoded_attrs = False

        for node in class_def.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                # Skip common attributes that aren't config
                if node.target.id in {
                    "logger",
                    "initialized",
                    "client",
                    "messages",
                    "context",
                }:
                    continue

                # Check if this looks like a config attribute
                if hasattr(node, "value") and node.value is not None:
                    self.add_issue(
                        f"Hardcoded attribute '{node.target.id}' in {class_def.name} ({plugin_path.parent})"
                    )
                    has_hardcoded_attrs = True

        return not has_hardcoded_attrs

    def check_initialize_cleanup(
        self, class_def: ast.ClassDef, plugin_path: Path
    ) -> bool:
        """Check if initialize and cleanup methods call super().

        Args:
            class_def: AST ClassDef to check
            plugin_path: Path to the plugin.yaml file

        Returns:
            True if methods are implemented correctly, False otherwise
        """
        has_initialize = False
        has_cleanup = False
        initialize_calls_super = False
        cleanup_calls_super = False

        for node in class_def.body:
            if isinstance(node, ast.AsyncFunctionDef):
                # Check initialize method
                if node.name == "initialize":
                    has_initialize = True

                    # Check if it calls super().initialize()
                    for stmt in ast.walk(node):
                        if (
                            isinstance(stmt, ast.Await)
                            and isinstance(stmt.value, ast.Call)
                            and isinstance(stmt.value.func, ast.Attribute)
                            and isinstance(stmt.value.func.value, ast.Call)
                            and isinstance(stmt.value.func.value.func, ast.Name)
                            and stmt.value.func.value.func.id == "super"
                            and stmt.value.func.attr == "initialize"
                        ):
                            initialize_calls_super = True
                            break

                # Check cleanup method
                elif node.name == "cleanup":
                    has_cleanup = True

                    # Check if it calls super().cleanup()
                    for stmt in ast.walk(node):
                        if (
                            isinstance(stmt, ast.Await)
                            and isinstance(stmt.value, ast.Call)
                            and isinstance(stmt.value.func, ast.Attribute)
                            and isinstance(stmt.value.func.value, ast.Call)
                            and isinstance(stmt.value.func.value.func, ast.Name)
                            and stmt.value.func.value.func.id == "super"
                            and stmt.value.func.attr == "cleanup"
                        ):
                            cleanup_calls_super = True
                            break

        if not has_initialize:
            self.add_issue(
                f"Missing initialize method in {class_def.name} ({plugin_path.parent})"
            )
            return False

        if not has_cleanup:
            self.add_issue(
                f"Missing cleanup method in {class_def.name} ({plugin_path.parent})"
            )
            return False

        if not initialize_calls_super:
            self.add_issue(
                f"initialize method in {class_def.name} ({plugin_path.parent}) does not call super().initialize()"
            )
            return False

        if not cleanup_calls_super:
            self.add_issue(
                f"cleanup method in {class_def.name} ({plugin_path.parent}) does not call super().cleanup()"
            )
            return False

        return True

    def check_config_usage(self, class_def: ast.ClassDef, plugin_path: Path) -> bool:
        """Check if a class uses self.config instead of direct attributes.

        Args:
            class_def: AST ClassDef to check
            plugin_path: Path to the plugin.yaml file

        Returns:
            True if config usage is correct, False otherwise
        """
        # Find all attribute accesses in the class
        config_accesses = 0
        direct_attribute_accesses = []

        for node in ast.walk(class_def):
            # Look for self.config.get() or self.config[] calls
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Attribute)
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "self"
                and node.func.value.attr == "config"
                and node.func.attr == "get"
            ):
                config_accesses += 1

            # Look for direct attribute access like self.api_key
            elif (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
                and node.attr
                not in {
                    "config",
                    "logger",
                    "initialized",
                    "client",
                    "messages",
                    "context",
                }
            ):
                direct_attribute_accesses.append(node.attr)

        # Report direct attribute accesses that might be config
        common_config_names = {
            "api_key",
            "model",
            "temperature",
            "max_tokens",
            "url",
            "endpoint",
        }
        suspicious_attrs = [
            attr for attr in direct_attribute_accesses if attr in common_config_names
        ]

        if suspicious_attrs:
            unique_attrs = set(suspicious_attrs)
            self.add_issue(
                f"Class {class_def.name} in {plugin_path.parent} directly accesses attributes that should use self.config: {', '.join(unique_attrs)}"
            )
            return False

        if config_accesses == 0:
            self.add_warning(
                f"Class {class_def.name} in {plugin_path.parent} does not appear to use self.config.get()"
            )

        return True

    def check_provider_class(
        self, plugin_path: Path, plugin_data: dict[str, Any]
    ) -> bool:
        """Validate the provider class for a plugin.

        Args:
            plugin_path: Path to the plugin.yaml file
            plugin_data: Plugin data from YAML

        Returns:
            True if provider is valid, False otherwise
        """
        # Get provider module and class
        entry_point = plugin_data.get("entry_point", "")
        if not entry_point or "." not in entry_point:
            return False

        module_name, class_name = entry_point.rsplit(".", 1)

        # Find the Python file
        python_file = plugin_path.parent / f"{module_name}.py"
        if not python_file.exists():
            self.add_issue(f"Provider file {python_file} does not exist")
            return False

        # Parse the Python file
        module_ast = self.parse_python_file(python_file)
        if not module_ast:
            return False

        # Find the provider class
        class_def = self.find_provider_class(module_ast, class_name)
        if not class_def:
            self.add_issue(f"Provider class {class_name} not found in {python_file}")
            return False

        # Check inheritance
        inheritance_ok = self.check_inheritance(class_def, plugin_path)

        # Check hardcoded attributes
        attributes_ok = self.check_hardcoded_attributes(class_def, plugin_path)

        # Check initialize and cleanup
        methods_ok = self.check_initialize_cleanup(class_def, plugin_path)

        # Check config usage
        config_ok = self.check_config_usage(class_def, plugin_path)

        return inheritance_ok and attributes_ok and methods_ok and config_ok

    def validate_plugin(self, plugin_path: Path) -> bool:
        """Validate a plugin.

        Args:
            plugin_path: Path to the plugin.yaml file

        Returns:
            True if plugin is valid, False otherwise
        """
        self.log(f"Validating {plugin_path}")

        # Reset issues for this plugin
        plugin_issues = len(self.issues)
        plugin_warnings = len(self.warnings)

        # Validate plugin.yaml
        plugin_data = self.validate_plugin_yaml(plugin_path)
        if not plugin_data:
            self.failed += 1
            return False

        # Store plugin data for later reference
        self.all_plugins.append({"path": plugin_path, "data": plugin_data})

        # Validate provider class
        provider_valid = self.check_provider_class(plugin_path, plugin_data)

        # Calculate result
        plugin_has_issues = len(self.issues) > plugin_issues
        plugin_has_warnings = len(self.warnings) > plugin_warnings

        if plugin_has_issues:
            self.log(f"Plugin {plugin_path} has ISSUES")
            self.failed += 1
            return False
        elif plugin_has_warnings:
            self.log(f"Plugin {plugin_path} has WARNINGS")
            self.passed += 1
            return True
        else:
            self.log(f"Plugin {plugin_path} is valid")
            self.passed += 1
            return True

    def validate_all_plugins(self) -> bool:
        """Validate all plugins.

        Returns:
            True if all plugins are valid, False otherwise
        """
        plugins = self.find_plugins()

        if not plugins:
            return False

        for plugin_path in plugins:
            try:
                self.validate_plugin(plugin_path)
            except Exception as e:
                self.add_issue(f"Error validating {plugin_path}: {e}")
                self.failed += 1

        return len(self.issues) == 0

    def print_summary(self) -> None:
        """Print a summary of validation results."""
        total = self.passed + self.failed + self.skipped

        try:
            print("\n" + "=" * 60)
            print(
                f"SUMMARY: {self.passed} passed, {self.failed} failed, {self.skipped} skipped, {total} total"
            )

            if self.warnings:
                print("\nWARNINGS:")
                for warning in self.warnings:
                    print(f"- {warning}")

            if self.issues:
                print("\nISSUES:")
                for issue in self.issues:
                    print(f"- {issue}")

            print("=" * 60)
        except BrokenPipeError:
            # Handle broken pipe when output is piped to another process
            sys.stderr.close()
            return


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate PepperPy plugins")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--fix",
        "-f",
        action="store_true",
        help="Automatically fix issues (not implemented)",
    )
    parser.add_argument(
        "--plugin", "-p", help="Validate a specific plugin", default=None
    )
    parser.add_argument("--output", "-o", help="Output file for results", default=None)
    args = parser.parse_args()

    # Redirect output to file if specified
    original_stdout = sys.stdout
    if args.output:
        try:
            sys.stdout = open(args.output, "w")
        except Exception as e:
            print(f"Error opening output file: {e}")
            return 1

    try:
        validator = PluginValidator(verbose=args.verbose, fix=args.fix)

        if args.plugin:
            # Validate a specific plugin
            plugin_path = Path(args.plugin)
            if not plugin_path.exists():
                print(f"Plugin {plugin_path} does not exist")
                return 1

            if plugin_path.is_dir():
                plugin_path = plugin_path / "plugin.yaml"

            if not plugin_path.exists():
                print(f"Plugin YAML {plugin_path} does not exist")
                return 1

            valid = validator.validate_plugin(plugin_path)
        else:
            # Validate all plugins
            valid = validator.validate_all_plugins()

        validator.print_summary()

        return 0 if valid else 1
    except BrokenPipeError:
        # Handle broken pipe error
        sys.stderr.close()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Restore original stdout if redirected
        if args.output:
            sys.stdout.close()
            sys.stdout = original_stdout


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
