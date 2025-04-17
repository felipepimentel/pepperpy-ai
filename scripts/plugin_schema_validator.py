#!/usr/bin/env python3
"""
Plugin Schema Validator for PepperPy.

This script validates plugin.yaml files against a standard schema definition,
ensuring all plugins follow the required format and contain necessary fields.
"""

import argparse
import glob
import json
import logging
import os
import sys
from typing import Any

import jsonschema
import yaml
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Standard plugin.yaml schema definition
PLUGIN_SCHEMA = {
    "type": "object",
    "required": [
        "name",
        "version",
        "description",
        "author",
        "plugin_type",
        "category",
        "provider_name",
        "entry_point",
        "config_schema",
    ],
    "properties": {
        "name": {
            "type": "string",
            "description": "Unique plugin name",
            "pattern": "^[a-zA-Z0-9_]+$",
        },
        "version": {
            "type": "string",
            "description": "Semantic version",
            "pattern": "^\\d+\\.\\d+\\.\\d+$",
        },
        "description": {"type": "string", "description": "Brief description"},
        "author": {"type": "string", "description": "Author information"},
        "plugin_type": {
            "type": "string",
            "description": "Domain (llm, content, etc)",
            "enum": [
                "agent",
                "cache",
                "content",
                "embeddings",
                "llm",
                "rag",
                "storage",
                "tool",
                "workflow",
            ],
        },
        "category": {"type": "string", "description": "Provider category"},
        "provider_name": {
            "type": "string",
            "description": "Provider name",
            "pattern": "^[a-z0-9_]+$",
        },
        "entry_point": {
            "type": "string",
            "description": "Implementation class path",
            "pattern": "^[a-zA-Z0-9_.]+$",
        },
        "min_framework_version": {
            "type": "string",
            "description": "Minimum framework version required",
            "pattern": "^\\d+\\.\\d+\\.\\d+$",
        },
        "max_framework_version": {
            "type": "string",
            "description": "Maximum framework version supported",
            "pattern": "^\\d+\\.\\d+\\.\\d+$",
        },
        "config_schema": {
            "type": "object",
            "description": "JSON Schema for configuration",
            "required": ["type", "properties"],
            "properties": {
                "type": {"type": "string", "enum": ["object"]},
                "properties": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["type", "description"],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "string",
                                    "integer",
                                    "number",
                                    "boolean",
                                    "array",
                                    "object",
                                ],
                            },
                            "description": {"type": "string"},
                            "default": {
                                "description": "Default value for the property"
                            },
                            "enum": {
                                "type": "array",
                                "description": "Enumeration of possible values",
                            },
                            "minimum": {
                                "type": "number",
                                "description": "Minimum value for numeric types",
                            },
                            "maximum": {
                                "type": "number",
                                "description": "Maximum value for numeric types",
                            },
                            "minLength": {
                                "type": "integer",
                                "description": "Minimum length for string types",
                            },
                            "maxLength": {
                                "type": "integer",
                                "description": "Maximum length for string types",
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Regex pattern for string types",
                            },
                            "items": {
                                "type": "object",
                                "description": "Schema for array items",
                            },
                            "properties": {
                                "type": "object",
                                "description": "Schema for object properties",
                            },
                        },
                    },
                },
                "required": {"type": "array", "items": {"type": "string"}},
            },
        },
        "default_config": {
            "type": "object",
            "description": "Default configuration values",
        },
        "examples": {
            "type": "array",
            "description": "Examples for testing the plugin",
            "items": {
                "type": "object",
                "required": ["name", "description", "input", "expected_output"],
                "properties": {
                    "name": {"type": "string", "description": "Example name"},
                    "description": {
                        "type": "string",
                        "description": "Example description",
                    },
                    "input": {"type": "object", "description": "Input data"},
                    "expected_output": {
                        "type": "object",
                        "description": "Expected output data",
                    },
                },
            },
            "minItems": 1,
        },
    },
}


class ValidationError:
    """Represents a validation error in a plugin.yaml file."""

    def __init__(
        self,
        plugin_path: str,
        error_message: str,
        error_path: list[str] = None,
        severity: str = "error",
        suggestion: str = None,
    ):
        """Initialize a validation error.

        Args:
            plugin_path: Path to the plugin directory
            error_message: Error message
            error_path: JSON path to the error location
            severity: Error severity (error, warning, info)
            suggestion: Suggestion for fixing the error
        """
        self.plugin_path = plugin_path
        self.error_message = error_message
        self.error_path = error_path or []
        self.severity = severity.lower()
        self.suggestion = suggestion

    def get_path_str(self) -> str:
        """Get string representation of the error path.

        Returns:
            String representation of the path
        """
        if not self.error_path:
            return ""

        path_str = ""
        for item in self.error_path:
            if isinstance(item, int):
                path_str += f"[{item}]"
            else:
                if path_str:
                    path_str += "."
                path_str += str(item)

        return path_str

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            String representation
        """
        color = {"error": Fore.RED, "warning": Fore.YELLOW, "info": Fore.BLUE}.get(
            self.severity, Fore.WHITE
        )

        path_str = self.get_path_str()

        result = (
            f"{color}{self.severity.upper()}{Style.RESET_ALL} in {self.plugin_path}"
        )
        if path_str:
            result += f" at {Fore.CYAN}{path_str}{Style.RESET_ALL}"

        result += f": {self.error_message}"

        if self.suggestion:
            result += f"\n  {Fore.GREEN}Suggestion:{Style.RESET_ALL} {self.suggestion}"

        return result


class SchemaValidator:
    """Validates plugin.yaml files against the standard schema."""

    def __init__(self, plugins_dir: str = "plugins") -> None:
        """Initialize validator.

        Args:
            plugins_dir: Base directory for plugins
        """
        self.plugins_dir = plugins_dir
        self.schema = PLUGIN_SCHEMA

        # Validator instance
        self.validator = jsonschema.Draft7Validator(self.schema)

    def find_plugins(self) -> list[str]:
        """Find all plugin directories with plugin.yaml files.

        Returns:
            List of plugin paths
        """
        plugin_dirs = []

        # Find all plugin.yaml files
        for plugin_yaml in glob.glob(
            f"{self.plugins_dir}/**/plugin.yaml", recursive=True
        ):
            plugin_dir = os.path.dirname(plugin_yaml)
            plugin_dirs.append(plugin_dir)

        return plugin_dirs

    def load_plugin_yaml(self, plugin_dir: str) -> dict[str, Any]:
        """Load plugin.yaml file.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Loaded YAML content

        Raises:
            FileNotFoundError: If plugin.yaml is not found
            yaml.YAMLError: If plugin.yaml is not valid YAML
        """
        yaml_path = os.path.join(plugin_dir, "plugin.yaml")

        with open(yaml_path) as f:
            return yaml.safe_load(f)

    def validate_plugin(self, plugin_dir: str) -> list[ValidationError]:
        """Validate a plugin.yaml file.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            List of validation errors
        """
        errors = []

        try:
            # Load plugin.yaml
            yaml_content = self.load_plugin_yaml(plugin_dir)

            # Basic validation using jsonschema
            for error in self.validator.iter_errors(yaml_content):
                path = list(error.path)

                suggestion = None
                if error.validator == "required":
                    missing = (
                        error.validator_value[0] if error.validator_value else None
                    )
                    if missing:
                        suggestion = f"Add the required field '{missing}'"

                elif error.validator == "enum":
                    valid_values = ", ".join([f"'{v}'" for v in error.validator_value])
                    suggestion = f"Use one of: {valid_values}"

                elif error.validator == "pattern":
                    if "version" in path:
                        suggestion = "Use semantic versioning (e.g., '0.1.0')"
                    elif "name" in path:
                        suggestion = "Use alphanumeric characters and underscores only"
                    elif "provider_name" in path:
                        suggestion = (
                            "Use lowercase alphanumeric characters and underscores only"
                        )
                    elif "entry_point" in path:
                        suggestion = "Use format 'module.ClassName' or 'ClassName'"

                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message=error.message,
                        error_path=path,
                        suggestion=suggestion,
                    )
                )

            # Additional custom validations
            self._validate_config_schema(plugin_dir, yaml_content, errors)
            self._validate_examples(plugin_dir, yaml_content, errors)
            self._validate_consistency(plugin_dir, yaml_content, errors)

        except FileNotFoundError:
            errors.append(
                ValidationError(
                    plugin_path=plugin_dir,
                    error_message="plugin.yaml not found",
                    suggestion="Create a plugin.yaml file in this directory",
                )
            )
        except yaml.YAMLError as e:
            errors.append(
                ValidationError(
                    plugin_path=plugin_dir,
                    error_message=f"Invalid YAML: {e}",
                    suggestion="Fix the YAML syntax",
                )
            )
        except Exception as e:
            errors.append(
                ValidationError(
                    plugin_path=plugin_dir,
                    error_message=f"Unexpected error: {e}",
                )
            )

        return errors

    def _validate_config_schema(
        self,
        plugin_dir: str,
        yaml_content: dict[str, Any],
        errors: list[ValidationError],
    ) -> None:
        """Validate the config_schema section.

        Args:
            plugin_dir: Path to plugin directory
            yaml_content: Loaded YAML content
            errors: List to append errors to
        """
        config_schema = yaml_content.get("config_schema", {})
        default_config = yaml_content.get("default_config", {})

        if not config_schema or not isinstance(config_schema, dict):
            return

        # Check that all defaults are in the schema
        for key, value in default_config.items():
            if key not in config_schema.get("properties", {}):
                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message=f"Default config key '{key}' not defined in config_schema",
                        error_path=["default_config", key],
                        suggestion=f"Add '{key}' to config_schema.properties",
                    )
                )

        # Check that required properties have no defaults
        required_props = config_schema.get("required", [])
        for prop in required_props:
            if prop in default_config:
                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message=f"Required property '{prop}' should not have a default value",
                        error_path=["config_schema", "required"],
                        severity="warning",
                        suggestion=f"Either remove '{prop}' from required or remove its default",
                    )
                )

        # Check that property types match their defaults
        properties = config_schema.get("properties", {})
        for key, prop_schema in properties.items():
            if key in default_config:
                default = default_config[key]
                prop_type = prop_schema.get("type")

                if prop_type == "string" and not isinstance(default, str):
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"Default for '{key}' should be a string",
                            error_path=["default_config", key],
                            suggestion="Change default to a string value",
                        )
                    )
                elif prop_type == "integer" and not isinstance(default, int):
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"Default for '{key}' should be an integer",
                            error_path=["default_config", key],
                            suggestion="Change default to an integer value",
                        )
                    )
                elif prop_type == "number" and not isinstance(default, (int, float)):
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"Default for '{key}' should be a number",
                            error_path=["default_config", key],
                            suggestion="Change default to a numeric value",
                        )
                    )
                elif prop_type == "boolean" and not isinstance(default, bool):
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"Default for '{key}' should be a boolean",
                            error_path=["default_config", key],
                            suggestion="Change default to true or false",
                        )
                    )
                elif prop_type == "array" and not isinstance(default, list):
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"Default for '{key}' should be an array",
                            error_path=["default_config", key],
                            suggestion="Change default to an array value",
                        )
                    )
                elif prop_type == "object" and not isinstance(default, dict):
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"Default for '{key}' should be an object",
                            error_path=["default_config", key],
                            suggestion="Change default to an object value",
                        )
                    )

    def _validate_examples(
        self,
        plugin_dir: str,
        yaml_content: dict[str, Any],
        errors: list[ValidationError],
    ) -> None:
        """Validate the examples section.

        Args:
            plugin_dir: Path to plugin directory
            yaml_content: Loaded YAML content
            errors: List to append errors to
        """
        examples = yaml_content.get("examples", [])

        if not examples:
            errors.append(
                ValidationError(
                    plugin_path=plugin_dir,
                    error_message="No examples defined",
                    error_path=["examples"],
                    suggestion="Add at least one example with name, description, input, and expected_output",
                )
            )
            return

        # Check for duplicate example names
        example_names = set()
        for i, example in enumerate(examples):
            name = example.get("name", "")
            if name in example_names:
                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message=f"Duplicate example name: '{name}'",
                        error_path=["examples", i, "name"],
                        suggestion="Use unique names for all examples",
                    )
                )
            else:
                example_names.add(name)

        # Check example outputs for expected format
        for i, example in enumerate(examples):
            output = example.get("expected_output", {})

            if "status" not in output:
                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message="Expected output should have a 'status' field",
                        error_path=["examples", i, "expected_output"],
                        suggestion="Add 'status': 'success' or 'status': 'error'",
                    )
                )

            # Warn if no result for success status
            if output.get("status") == "success" and "result" not in output:
                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message="Success output should have a 'result' field",
                        error_path=["examples", i, "expected_output"],
                        severity="warning",
                        suggestion="Add a 'result' field to the expected output",
                    )
                )

            # Warn if no error message for error status
            if output.get("status") == "error" and "message" not in output:
                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message="Error output should have a 'message' field",
                        error_path=["examples", i, "expected_output"],
                        severity="warning",
                        suggestion="Add a 'message' field to the expected output",
                    )
                )

    def _validate_consistency(
        self,
        plugin_dir: str,
        yaml_content: dict[str, Any],
        errors: list[ValidationError],
    ) -> None:
        """Validate consistency with file structure.

        Args:
            plugin_dir: Path to plugin directory
            yaml_content: Loaded YAML content
            errors: List to append errors to
        """
        # Check that entry_point refers to an existing class
        entry_point = yaml_content.get("entry_point", "")
        if entry_point:
            # Check if provider.py exists
            provider_path = os.path.join(plugin_dir, "provider.py")
            if not os.path.isfile(provider_path):
                errors.append(
                    ValidationError(
                        plugin_path=plugin_dir,
                        error_message="provider.py not found but referenced in entry_point",
                        error_path=["entry_point"],
                        suggestion="Create provider.py with the referenced class",
                    )
                )
            else:
                # Try to parse the file to find the class
                try:
                    with open(provider_path) as f:
                        content = f.read()

                    # Simple check for class definition
                    class_name = entry_point.split(".")[-1]
                    if f"class {class_name}" not in content:
                        errors.append(
                            ValidationError(
                                plugin_path=plugin_dir,
                                error_message=f"Class '{class_name}' not found in provider.py",
                                error_path=["entry_point"],
                                suggestion=f"Define class {class_name} in provider.py",
                            )
                        )
                except Exception:
                    pass  # Skip detailed validation if file can't be read

        # Verify plugin directory structure matches metadata
        try:
            # Extract expected plugin path components
            rel_path = os.path.relpath(plugin_dir, self.plugins_dir)
            path_parts = rel_path.split(os.path.sep)

            if len(path_parts) == 3:
                domain, category, provider = path_parts

                # Check plugin_type matches domain
                plugin_type = yaml_content.get("plugin_type")
                if plugin_type and plugin_type != domain:
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"plugin_type '{plugin_type}' doesn't match directory structure domain '{domain}'",
                            error_path=["plugin_type"],
                            suggestion=f"Change plugin_type to '{domain}'",
                        )
                    )

                # Check category matches directory
                yaml_category = yaml_content.get("category")
                if yaml_category and yaml_category != category:
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"category '{yaml_category}' doesn't match directory structure category '{category}'",
                            error_path=["category"],
                            suggestion=f"Change category to '{category}'",
                        )
                    )

                # Check provider_name matches directory
                provider_name = yaml_content.get("provider_name")
                if provider_name and provider_name != provider:
                    errors.append(
                        ValidationError(
                            plugin_path=plugin_dir,
                            error_message=f"provider_name '{provider_name}' doesn't match directory name '{provider}'",
                            error_path=["provider_name"],
                            suggestion=f"Change provider_name to '{provider}'",
                        )
                    )
        except Exception:
            pass  # Skip if path parsing fails

    def validate_all_plugins(self) -> dict[str, list[ValidationError]]:
        """Validate all plugins.

        Returns:
            Dictionary mapping plugin paths to validation errors
        """
        results = {}

        # Find all plugins
        plugin_dirs = self.find_plugins()

        for plugin_dir in plugin_dirs:
            logger.info(f"Validating {plugin_dir}")

            # Validate plugin
            errors = self.validate_plugin(plugin_dir)

            results[plugin_dir] = errors

        return results

    def generate_report(
        self, results: dict[str, list[ValidationError]], json_output: bool = False
    ) -> str:
        """Generate a validation report.

        Args:
            results: Validation results
            json_output: Whether to output in JSON format

        Returns:
            Report content
        """
        if json_output:
            # Generate JSON report
            json_data = {"plugins": {}}

            for plugin_dir, errors in results.items():
                plugin_errors = []

                for error in errors:
                    plugin_errors.append(
                        {
                            "message": error.error_message,
                            "path": ".".join(str(p) for p in error.error_path)
                            if error.error_path
                            else None,
                            "severity": error.severity,
                            "suggestion": error.suggestion,
                        }
                    )

                json_data["plugins"][plugin_dir] = plugin_errors

            return json.dumps(json_data, indent=2)

        else:
            # Generate text report
            report = []

            # Count errors by severity
            total_plugins = len(results)
            total_errors = sum(len(errors) for errors in results.values())
            error_plugins = sum(
                1
                for errors in results.values()
                if any(e.severity == "error" for e in errors)
            )
            warning_plugins = sum(
                1
                for errors in results.values()
                if any(e.severity == "warning" for e in errors)
            )

            # Generate summary
            report.append("Plugin Schema Validation Report")
            report.append("==============================")
            report.append("")
            report.append(f"Total plugins: {total_plugins}")
            report.append(f"Plugins with errors: {error_plugins}")
            report.append(f"Plugins with warnings: {warning_plugins}")
            report.append(f"Total issues: {total_errors}")
            report.append("")

            # Generate details
            for plugin_dir, errors in sorted(results.items()):
                if not errors:
                    continue

                report.append(f"Plugin: {plugin_dir}")
                report.append("-" * (len(plugin_dir) + 8))

                for error in errors:
                    report.append(f"  {error}")

                report.append("")

            return "\n".join(report)


def main() -> int:
    """Run the schema validator.

    Returns:
        Exit code (0 for success, non-zero otherwise)
    """
    parser = argparse.ArgumentParser(
        description="Validate plugin.yaml files against standard schema"
    )
    parser.add_argument(
        "-d", "--plugins-dir", default="plugins", help="Base plugins directory"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file for report (default: stdout)",
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="Output in JSON format"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-f",
        "--fail-on-warnings",
        action="store_true",
        help="Return non-zero exit code for warnings",
    )
    parser.add_argument("-s", "--single", help="Validate a single plugin directory")
    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create validator
    validator = SchemaValidator(plugins_dir=args.plugins_dir)

    try:
        # Validate plugins
        if args.single:
            # Validate a single plugin
            plugin_dir = args.single
            if not os.path.isdir(plugin_dir):
                logger.error(f"Error: {plugin_dir} is not a directory")
                return 1

            results = {plugin_dir: validator.validate_plugin(plugin_dir)}
        else:
            # Validate all plugins
            results = validator.validate_all_plugins()

        # Generate report
        report = validator.generate_report(results, args.json)

        # Output report
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report written to {args.output}")
        else:
            print(report)

        # Check for errors or warnings
        has_errors = any(
            any(e.severity == "error" for e in errors) for errors in results.values()
        )
        has_warnings = any(
            any(e.severity == "warning" for e in errors) for errors in results.values()
        )

        if has_errors:
            return 1
        elif has_warnings and args.fail_on_warnings:
            return 1
        else:
            return 0

    except Exception as e:
        logger.error(f"Error validating plugins: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
