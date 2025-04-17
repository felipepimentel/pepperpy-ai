#!/usr/bin/env python3
"""
Plugin Validator for PepperPy.

This script validates plugins against architectural requirements and best practices.
"""

import argparse
import ast
import glob
import logging
import os
import sys
from dataclasses import dataclass, field
from enum import Enum

import yaml


class IssueLevel(Enum):
    """Issue severity level."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a plugin."""

    plugin_path: str
    message: str
    level: IssueLevel
    file_path: str | None = None
    line_number: int | None = None

    def __str__(self) -> str:
        """Format issue for display."""
        location = f"{self.file_path}" if self.file_path else self.plugin_path
        if self.line_number:
            location = f"{location}:{self.line_number}"

        return f"[{self.level.value.upper()}] {location}: {self.message}"


@dataclass
class PluginValidationResult:
    """Results of validating a plugin."""

    plugin_path: str
    issues: list[ValidationIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add_issue(
        self,
        message: str,
        level: IssueLevel,
        file_path: str | None = None,
        line_number: int | None = None,
    ) -> None:
        """Add a validation issue."""
        issue = ValidationIssue(
            plugin_path=self.plugin_path,
            message=message,
            level=level,
            file_path=file_path,
            line_number=line_number,
        )
        self.issues.append(issue)

        if level == IssueLevel.ERROR:
            self.error_count += 1
        elif level == IssueLevel.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1

    @property
    def has_errors(self) -> bool:
        """Check if validation found errors."""
        return self.error_count > 0

    def __str__(self) -> str:
        """Format validation result for display."""
        if not self.issues:
            return f"✅ {self.plugin_path}: No issues found"

        result = [
            f"⚠️ {self.plugin_path}: Found {len(self.issues)} issues "
            f"({self.error_count} errors, {self.warning_count} warnings, "
            f"{self.info_count} info)"
        ]

        for issue in self.issues:
            result.append(f"  {issue}")

        return "\n".join(result)


class PluginValidator:
    """Validates PepperPy plugins against architectural requirements."""

    REQUIRED_YAML_FIELDS = {
        "name",
        "version",
        "description",
        "author",
        "plugin_type",
        "category",
        "provider_name",
        "entry_point",
    }

    RECOMMENDED_YAML_FIELDS = {"config_schema", "default_config", "examples"}

    PLUGIN_FILES = {
        "plugin.yaml": True,  # Required
        "provider.py": True,  # Required
        "__init__.py": True,  # Required
        "requirements.txt": False,  # Recommended
        "README.md": False,  # Recommended
    }

    def __init__(self, plugins_dir: str = "plugins") -> None:
        """Initialize validator.

        Args:
            plugins_dir: Base directory for plugins
        """
        self.plugins_dir = plugins_dir
        self.logger = logging.getLogger(__name__)

    def find_plugins(self) -> list[str]:
        """Find all plugin directories."""
        plugin_dirs = []

        # Find all plugin.yaml files and use their directory as plugin root
        for plugin_yaml in glob.glob(
            f"{self.plugins_dir}/**/plugin.yaml", recursive=True
        ):
            plugin_dir = os.path.dirname(plugin_yaml)
            plugin_dirs.append(plugin_dir)

        return plugin_dirs

    def validate_plugin_structure(self, plugin_path: str) -> PluginValidationResult:
        """Validate plugin directory structure and required files.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Validation result
        """
        result = PluginValidationResult(plugin_path=plugin_path)

        # Check for required files
        for filename, required in self.PLUGIN_FILES.items():
            file_path = os.path.join(plugin_path, filename)
            if not os.path.exists(file_path):
                level = IssueLevel.ERROR if required else IssueLevel.WARNING
                message = f"Missing {'required' if required else 'recommended'} file: {filename}"
                result.add_issue(message, level, file_path=file_path)

        return result

    def validate_plugin_yaml(self, plugin_path: str) -> PluginValidationResult:
        """Validate plugin.yaml content.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Validation result
        """
        result = PluginValidationResult(plugin_path=plugin_path)
        yaml_path = os.path.join(plugin_path, "plugin.yaml")

        if not os.path.exists(yaml_path):
            result.add_issue(
                "Missing plugin.yaml", IssueLevel.ERROR, file_path=yaml_path
            )
            return result

        try:
            with open(yaml_path) as f:
                plugin_data = yaml.safe_load(f)

            if not plugin_data:
                result.add_issue(
                    "Empty plugin.yaml", IssueLevel.ERROR, file_path=yaml_path
                )
                return result

            # Check required fields
            for field in self.REQUIRED_YAML_FIELDS:
                if field not in plugin_data:
                    result.add_issue(
                        f"Missing required field: {field}",
                        IssueLevel.ERROR,
                        file_path=yaml_path,
                    )
                elif not plugin_data[field]:
                    result.add_issue(
                        f"Empty required field: {field}",
                        IssueLevel.ERROR,
                        file_path=yaml_path,
                    )

            # Check recommended fields
            for field in self.RECOMMENDED_YAML_FIELDS:
                if field not in plugin_data:
                    result.add_issue(
                        f"Missing recommended field: {field}",
                        IssueLevel.WARNING,
                        file_path=yaml_path,
                    )

            # Validate name format
            if plugin_data.get("name"):
                name_parts = plugin_data["name"].split("/")
                if len(name_parts) < 2:
                    result.add_issue(
                        f"Invalid name format: {plugin_data['name']}. "
                        f"Expected format: domain/provider or domain/category/provider",
                        IssueLevel.ERROR,
                        file_path=yaml_path,
                    )

            # Validate entry_point
            if plugin_data.get("entry_point"):
                entry_point = plugin_data["entry_point"]
                if "." not in entry_point:
                    result.add_issue(
                        f"Invalid entry_point format: {entry_point}. "
                        f"Expected format: module.ClassName",
                        IssueLevel.ERROR,
                        file_path=yaml_path,
                    )

            # Check for examples
            if plugin_data.get("examples"):
                if not isinstance(plugin_data["examples"], list):
                    result.add_issue(
                        "Invalid examples format. Expected list of examples.",
                        IssueLevel.ERROR,
                        file_path=yaml_path,
                    )
                else:
                    for i, example in enumerate(plugin_data["examples"]):
                        if not isinstance(example, dict):
                            result.add_issue(
                                f"Invalid example at index {i}. Expected dictionary.",
                                IssueLevel.ERROR,
                                file_path=yaml_path,
                            )
                            continue

                        for field in ["name", "input"]:
                            if field not in example:
                                result.add_issue(
                                    f"Example at index {i} missing required field: {field}",
                                    IssueLevel.ERROR,
                                    file_path=yaml_path,
                                )

                        if "expected_output" not in example:
                            result.add_issue(
                                f"Example at index {i} missing recommended field: expected_output",
                                IssueLevel.WARNING,
                                file_path=yaml_path,
                            )

        except yaml.YAMLError as e:
            result.add_issue(
                f"Invalid YAML: {e}", IssueLevel.ERROR, file_path=yaml_path
            )
        except Exception as e:
            result.add_issue(
                f"Error validating plugin.yaml: {e}",
                IssueLevel.ERROR,
                file_path=yaml_path,
            )

        return result

    def validate_provider_implementation(
        self, plugin_path: str
    ) -> PluginValidationResult:
        """Validate provider.py implementation.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Validation result
        """
        result = PluginValidationResult(plugin_path=plugin_path)
        provider_path = os.path.join(plugin_path, "provider.py")

        if not os.path.exists(provider_path):
            result.add_issue(
                "Missing provider.py", IssueLevel.ERROR, file_path=provider_path
            )
            return result

        try:
            with open(provider_path) as f:
                code = f.read()

            tree = ast.parse(code)

            # Find provider class
            provider_class = None
            domain_provider_imported = False
            base_plugin_provider_imported = False

            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.ImportFrom):
                    if node.module and "pepperpy" in node.module:
                        for name in node.names:
                            if "Provider" in name.name and "Plugin" not in name.name:
                                domain_provider_imported = True
                            if (
                                "PluginProvider" in name.name
                                or "BasePluginProvider" in name.name
                            ):
                                base_plugin_provider_imported = True

                # Find provider class
                if isinstance(node, ast.ClassDef):
                    # Check for provider-like name
                    if "Provider" in node.name:
                        provider_class = node

                        # Check inheritance
                        domain_inherited = False
                        plugin_inherited = False

                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                if "Provider" in base.id and "Plugin" not in base.id:
                                    domain_inherited = True
                                if (
                                    "PluginProvider" in base.id
                                    or "BasePluginProvider" in base.id
                                ):
                                    plugin_inherited = True
                            elif isinstance(base, ast.Attribute):
                                if (
                                    "Provider" in base.attr
                                    and "Plugin" not in base.attr
                                ):
                                    domain_inherited = True
                                if (
                                    "PluginProvider" in base.attr
                                    or "BasePluginProvider" in base.attr
                                ):
                                    plugin_inherited = True

                        if not domain_inherited:
                            result.add_issue(
                                f"Provider class {node.name} does not inherit from domain provider",
                                IssueLevel.ERROR,
                                file_path=provider_path,
                                line_number=node.lineno,
                            )

                        if not plugin_inherited:
                            result.add_issue(
                                f"Provider class {node.name} does not inherit from BasePluginProvider",
                                IssueLevel.ERROR,
                                file_path=provider_path,
                                line_number=node.lineno,
                            )

            if not domain_provider_imported:
                result.add_issue(
                    "Missing import of domain provider class",
                    IssueLevel.ERROR,
                    file_path=provider_path,
                )

            if not base_plugin_provider_imported:
                result.add_issue(
                    "Missing import of BasePluginProvider",
                    IssueLevel.ERROR,
                    file_path=provider_path,
                )

            if not provider_class:
                result.add_issue(
                    "No provider class found in provider.py",
                    IssueLevel.ERROR,
                    file_path=provider_path,
                )
                return result

            # Check for initialize and cleanup methods
            initialize_method = None
            cleanup_method = None
            execute_method = None

            for node in ast.walk(provider_class):
                if isinstance(node, ast.AsyncFunctionDef):
                    if node.name == "initialize":
                        initialize_method = node
                    elif node.name == "cleanup":
                        cleanup_method = node
                    elif node.name == "execute":
                        execute_method = node

            if not initialize_method:
                result.add_issue(
                    "Missing async initialize() method",
                    IssueLevel.ERROR,
                    file_path=provider_path,
                )
            else:
                # Check for initialization flag check
                has_init_check = False
                for node in ast.walk(initialize_method):
                    if isinstance(node, ast.If):
                        for child in ast.walk(node.test):
                            if (
                                isinstance(child, ast.Name)
                                and child.id == "initialized"
                            ):
                                has_init_check = True
                                break

                if not has_init_check:
                    result.add_issue(
                        "initialize() method does not check initialized flag",
                        IssueLevel.WARNING,
                        file_path=provider_path,
                        line_number=initialize_method.lineno,
                    )

            if not cleanup_method:
                result.add_issue(
                    "Missing async cleanup() method",
                    IssueLevel.ERROR,
                    file_path=provider_path,
                )

            if not execute_method:
                result.add_issue(
                    "Missing async execute() method",
                    IssueLevel.ERROR,
                    file_path=provider_path,
                )

        except SyntaxError as e:
            result.add_issue(
                f"Invalid Python syntax: {e}", IssueLevel.ERROR, file_path=provider_path
            )
        except Exception as e:
            result.add_issue(
                f"Error validating provider.py: {e}",
                IssueLevel.ERROR,
                file_path=provider_path,
            )

        return result

    def validate_plugin(self, plugin_path: str) -> PluginValidationResult:
        """Validate a plugin directory.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Combined validation result
        """
        path_result = self.validate_plugin_structure(plugin_path)
        yaml_result = self.validate_plugin_yaml(plugin_path)
        provider_result = self.validate_provider_implementation(plugin_path)

        # Combine results
        result = PluginValidationResult(plugin_path=plugin_path)
        for partial_result in [path_result, yaml_result, provider_result]:
            result.issues.extend(partial_result.issues)
            result.error_count += partial_result.error_count
            result.warning_count += partial_result.warning_count
            result.info_count += partial_result.info_count

        return result

    def validate_all_plugins(self) -> list[PluginValidationResult]:
        """Validate all plugins in the plugins directory.

        Returns:
            List of validation results
        """
        plugin_paths = self.find_plugins()
        results = []

        for plugin_path in plugin_paths:
            results.append(self.validate_plugin(plugin_path))

        return results


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
    """Run the validator.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Validate PepperPy plugins against architectural requirements"
    )
    parser.add_argument(
        "-d", "--plugins-dir", default="plugins", help="Base plugins directory"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="Attempt to fix issues (not implemented yet)",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)

    validator = PluginValidator(plugins_dir=args.plugins_dir)
    results = validator.validate_all_plugins()

    # Display results
    error_count = 0
    warning_count = 0
    plugin_count = len(results)
    plugins_with_errors = 0

    for result in results:
        print(result)
        print()  # Empty line for readability

        error_count += result.error_count
        warning_count += result.warning_count
        if result.has_errors:
            plugins_with_errors += 1

    # Summary
    print(f"Validated {plugin_count} plugins")
    print(f"Found {error_count} errors and {warning_count} warnings")
    print(f"{plugins_with_errors} plugins have errors that need to be fixed")

    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
