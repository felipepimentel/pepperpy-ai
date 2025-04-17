#!/usr/bin/env python3
"""
Script to create a new plugin from templates.

This script takes care of:
1. Creating the necessary directory structure
2. Copying and customizing template files
3. Setting up plugin configuration
4. Creating test files
"""

import argparse
import json
import logging
import os
import re
import sys
from typing import Any

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
PLUGINS_DIR = "plugins"
TEMPLATES_DIR = "templates"
PLUGIN_TEMPLATE_DIR = f"{TEMPLATES_DIR}/plugin_template"
TESTS_TEMPLATE_DIR = f"{TEMPLATES_DIR}/plugin_tests_template"


def validate_plugin_path(plugin_path: str) -> bool:
    """
    Validates that the plugin path follows the domain/category/provider format.

    Args:
        plugin_path: Path in format domain/category/provider

    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    parts = plugin_path.strip("/").split("/")

    if len(parts) != 3:
        raise ValueError(
            f"Plugin path must have exactly 3 parts (domain/category/provider), got {len(parts)}: {plugin_path}"
        )

    # Check if each part is a valid Python identifier/package name
    for part in parts:
        if not re.match(r"^[a-z][a-z0-9_]*$", part):
            raise ValueError(
                f"Each part of the plugin path must be lowercase, start with a letter, "
                f"and contain only letters, numbers, and underscores. Invalid part: '{part}'"
            )

    # Check if this plugin already exists
    full_path = os.path.join(PLUGINS_DIR, *parts)
    if os.path.exists(full_path):
        raise ValueError(f"Plugin already exists at {full_path}")

    return True


def parse_plugin_path(plugin_path: str) -> tuple[str, str, str]:
    """
    Parse the plugin path into its components.

    Args:
        plugin_path: Path in format domain/category/provider

    Returns:
        Tuple[str, str, str]: (domain, category, provider)
    """
    parts = plugin_path.strip("/").split("/")
    return parts[0], parts[1], parts[2]


def create_plugin_directory(plugin_path: str) -> str:
    """
    Creates the directory structure for the plugin.

    Args:
        plugin_path: Path in format domain/category/provider

    Returns:
        str: Full path to the created plugin directory
    """
    domain, category, provider = parse_plugin_path(plugin_path)

    # Create domain directory if it doesn't exist
    domain_dir = os.path.join(PLUGINS_DIR, domain)
    os.makedirs(domain_dir, exist_ok=True)

    # Create category directory if it doesn't exist
    category_dir = os.path.join(domain_dir, category)
    os.makedirs(category_dir, exist_ok=True)

    # Create provider directory
    provider_dir = os.path.join(category_dir, provider)
    os.makedirs(provider_dir)

    logger.info(f"Created plugin directory structure at {provider_dir}")
    return provider_dir


def parse_config_option(option_str: str) -> tuple[str, str, Any, str]:
    """
    Parse a config option string in format name:type:default:description

    Args:
        option_str: String in format name:type:default:description

    Returns:
        Tuple[str, str, Any, str]: (name, type, default, description)
    """
    parts = option_str.split(":", 3)
    if len(parts) != 4:
        raise ValueError(
            f"Config option must be in format name:type:default:description, got: {option_str}"
        )

    name, type_str, default_str, description = parts

    # Convert default to the appropriate type
    default: Any

    if type_str == "str":
        default = default_str
    elif type_str == "int":
        default = int(default_str)
    elif type_str == "float":
        default = float(default_str)
    elif type_str == "bool":
        default = default_str.lower() in ("true", "yes", "1")
    elif type_str == "list" or type_str == "array":
        if default_str.startswith("[") and default_str.endswith("]"):
            default = json.loads(default_str)
        else:
            default = default_str.split(",") if default_str else []
    elif type_str == "object" or type_str == "dict":
        if default_str.startswith("{") and default_str.endswith("}"):
            default = json.loads(default_str)
        else:
            default = {}
    else:
        default = default_str
        logger.warning(f"Unknown type {type_str}, using default as string")

    return name, type_str, default, description


def process_template_file(
    template_path: str, output_path: str, replacements: dict[str, str]
) -> None:
    """
    Process a template file with string replacements.

    Args:
        template_path: Path to template file
        output_path: Path to write processed file
        replacements: Dictionary of replacements {placeholder: value}
    """
    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    # Replace placeholders
    for placeholder, value in replacements.items():
        content = content.replace(f"{{{{{placeholder}}}}}", value)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Created {output_path}")


def process_yaml_template(
    template_path: str,
    output_path: str,
    replacements: dict[str, str],
    config_options: list[tuple[str, str, Any, str]] | None = None,
) -> None:
    """
    Process a YAML template file with structured updates.

    Args:
        template_path: Path to template YAML file
        output_path: Path to write processed file
        replacements: Dictionary of replacements {placeholder: value}
        config_options: List of config options (name, type, default, description)
    """
    with open(template_path, encoding="utf-8") as f:
        yaml_content = yaml.safe_load(f)

    # Replace string placeholders in all fields
    yaml_str = yaml.dump(yaml_content)
    for placeholder, value in replacements.items():
        yaml_str = yaml_str.replace(f"{{{{{placeholder}}}}}", value)

    yaml_content = yaml.safe_load(yaml_str)

    # Add config options if provided
    if config_options:
        # Create config schema
        config_schema = {"type": "object", "properties": {}, "required": []}
        default_config = {}

        for name, type_str, default, description in config_options:
            # Map Python types to JSON Schema types
            if type_str == "str":
                json_type = "string"
            elif type_str == "int":
                json_type = "integer"
            elif type_str == "float":
                json_type = "number"
            elif type_str == "bool":
                json_type = "boolean"
            elif type_str in ("list", "array"):
                json_type = "array"
            elif type_str in ("object", "dict"):
                json_type = "object"
            else:
                json_type = "string"
                logger.warning(f"Unknown type {type_str}, using string in schema")

            # Add property to schema
            property_schema = {"type": json_type, "description": description}
            if default is not None:
                property_schema["default"] = default

            config_schema["properties"][name] = property_schema

            # Add to default config if there's a default value
            if default is not None:
                default_config[name] = default

        # Add to YAML
        yaml_content["config_schema"] = config_schema

        # Only add default_config if we have default values
        if default_config:
            yaml_content["default_config"] = default_config

    # Write updated YAML
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, sort_keys=False)

    logger.info(f"Created {output_path}")


def generate_provider_class_name(provider: str) -> str:
    """
    Generate a class name for the provider based on the provider name.

    Args:
        provider: Provider name (snake_case)

    Returns:
        str: Provider class name (PascalCase)
    """
    return "".join(part.capitalize() for part in provider.split("_")) + "Provider"


def generate_description(domain: str, provider: str) -> str:
    """
    Generate a description for the plugin based on its domain and provider.

    Args:
        domain: Plugin domain
        provider: Provider name

    Returns:
        str: Generated description
    """
    domain_desc = {
        "agent": "Agent implementation",
        "cache": "Cache provider",
        "core": "Core system component",
        "data": "Data handling component",
        "rag": "Retrieval-Augmented Generation component",
        "storage": "Storage provider",
        "tool": "Tool implementation",
        "workflow": "Workflow implementation",
    }

    domain_text = domain_desc.get(domain, f"{domain} implementation")
    provider_text = " ".join(p.capitalize() for p in provider.split("_"))

    return f"{provider_text} {domain_text}"


def copy_test_templates(plugin_path: str, provider_class_name: str) -> None:
    """
    Copy test templates to the appropriate location.

    Args:
        plugin_path: Path in format domain/category/provider
        provider_class_name: Name of the provider class
    """
    domain, category, provider = parse_plugin_path(plugin_path)

    # Create test directory
    test_dir = os.path.join("tests", domain, category, provider)
    os.makedirs(test_dir, exist_ok=True)

    # Process template files
    for template_file in os.listdir(TESTS_TEMPLATE_DIR):
        template_path = os.path.join(TESTS_TEMPLATE_DIR, template_file)
        if os.path.isfile(template_path):
            target_name = template_file.replace("provider", provider).replace(
                "ProviderClass", provider_class_name
            )
            target_path = os.path.join(test_dir, target_name)

            # Replace placeholders
            replacements = {
                "plugin_path": plugin_path,
                "domain": domain,
                "category": category,
                "provider": provider,
                "provider_class": provider_class_name,
            }

            process_template_file(template_path, target_path, replacements)

    logger.info(f"Created test files in {test_dir}")


def create_plugin(
    plugin_path: str,
    provider_class: str | None = None,
    description: str | None = None,
    author: str = "PepperPy Team",
    config_options: list[str] | None = None,
) -> str:
    """
    Create a new plugin from templates.

    Args:
        plugin_path: Path in format domain/category/provider
        provider_class: Name of the provider class (defaults to derived from provider name)
        description: Plugin description (defaults to generated based on domain/provider)
        author: Plugin author
        config_options: List of config options in format name:type:default:description

    Returns:
        str: Path to the created plugin directory
    """
    # Validate plugin path
    validate_plugin_path(plugin_path)

    # Parse path components
    domain, category, provider = parse_plugin_path(plugin_path)

    # Generate provider class name if not provided
    if not provider_class:
        provider_class = generate_provider_class_name(provider)

    # Generate description if not provided
    if not description:
        description = generate_description(domain, provider)

    # Create directory structure
    plugin_dir = create_plugin_directory(plugin_path)

    # Process configuration options if provided
    parsed_config_options = None
    if config_options:
        parsed_config_options = [
            parse_config_option(option) for option in config_options
        ]

    # Create replacements dictionary for templates
    replacements = {
        "plugin_path": plugin_path,
        "domain": domain,
        "category": category,
        "provider": provider,
        "provider_class": provider_class,
        "description": description,
        "author": author,
    }

    # Process each template file
    for template_file in os.listdir(PLUGIN_TEMPLATE_DIR):
        template_path = os.path.join(PLUGIN_TEMPLATE_DIR, template_file)
        if os.path.isfile(template_path):
            target_path = os.path.join(plugin_dir, template_file)

            # Handle YAML files specially
            if template_file.endswith(".yaml") or template_file.endswith(".yml"):
                process_yaml_template(
                    template_path, target_path, replacements, parsed_config_options
                )
            else:
                process_template_file(template_path, target_path, replacements)

    # Create test files
    copy_test_templates(plugin_path, provider_class)

    logger.info(f"Plugin created successfully at {plugin_dir}")
    return plugin_dir


def main():
    """Main function to parse arguments and create the plugin."""
    parser = argparse.ArgumentParser(description="Create a new plugin from templates.")

    # Required arguments
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin in format domain/category/provider",
    )

    # Optional arguments
    parser.add_argument(
        "--provider-class",
        help="Name of the provider class (defaults to derived from provider name)",
    )
    parser.add_argument(
        "--description",
        help="Plugin description (defaults to generated based on domain/provider)",
    )
    parser.add_argument(
        "--author",
        default="PepperPy Team",
        help="Plugin author (defaults to 'PepperPy Team')",
    )
    parser.add_argument(
        "--config-option",
        action="append",
        dest="config_options",
        help="Config option in format name:type:default:description "
        "(can be specified multiple times)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Create the plugin
        plugin_dir = create_plugin(
            args.plugin_path,
            args.provider_class,
            args.description,
            args.author,
            args.config_options,
        )

        # Print success message
        print(f"\nPlugin created successfully at: {plugin_dir}")
        print("\nNext steps:")
        print("1. Implement your provider in provider.py")
        print("2. Add examples to plugin.yaml")
        print("3. Add tests in the created test files")
        print("4. Run validation: python scripts/plugin_validator.py")

        return 0

    except Exception as e:
        logger.error(f"Error creating plugin: {e!s}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
