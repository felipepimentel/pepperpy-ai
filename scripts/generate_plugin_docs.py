#!/usr/bin/env python3
"""
Plugin Documentation Generator for PepperPy.

This script generates documentation for plugins based on their metadata,
configuration schema, and examples defined in plugin.yaml.
"""

import argparse
import ast
import glob
import json
import logging
import os
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


class DocGenerator:
    """Generates documentation for plugins."""

    def __init__(
        self, plugins_dir: str = "plugins", output_dir: str = "docs/plugins"
    ) -> None:
        """Initialize generator.

        Args:
            plugins_dir: Base directory for plugins
            output_dir: Directory to write documentation
        """
        self.plugins_dir = plugins_dir
        self.output_dir = output_dir

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

    def load_plugin_metadata(self, plugin_dir: str) -> dict[str, Any]:
        """Load plugin metadata from plugin.yaml.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Plugin metadata
        """
        yaml_path = os.path.join(plugin_dir, "plugin.yaml")

        try:
            with open(yaml_path) as f:
                metadata = yaml.safe_load(f)
            return metadata
        except Exception as e:
            logger.error(f"Error loading metadata from {yaml_path}: {e}")
            return {}

    def extract_provider_capabilities(self, plugin_dir: str) -> dict[str, Any]:
        """Extract capabilities and methods from provider.py.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Dictionary of capabilities and methods
        """
        provider_path = os.path.join(plugin_dir, "provider.py")
        if not os.path.exists(provider_path):
            return {}

        try:
            with open(provider_path) as f:
                content = f.read()

            # Parse the Python code
            tree = ast.parse(content)

            # Find the provider class
            provider_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    provider_class = node
                    break

            if not provider_class:
                return {}

            # Extract method information
            methods = []
            for node in provider_class.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    # Get docstring if available
                    docstring = ast.get_docstring(node)

                    # Get parameters
                    params = []
                    for arg in node.args.args:
                        if arg.arg != "self":
                            params.append(arg.arg)

                    methods.append(
                        {"name": node.name, "docstring": docstring, "params": params}
                    )

            # Extract capabilities property or method
            capabilities = {}
            for node in provider_class.body:
                if isinstance(node, ast.FunctionDef) and node.name == "capabilities":
                    # This is likely a property getter
                    for sub_node in ast.walk(node):
                        if isinstance(sub_node, ast.Return):
                            if isinstance(sub_node.value, ast.Dict):
                                # Try to extract static capabilities
                                for i, key_node in enumerate(sub_node.value.keys):
                                    if hasattr(key_node, "value") and hasattr(
                                        sub_node.value.values[i], "value"
                                    ):
                                        key_val = key_node.value
                                        val_val = sub_node.value.values[i].value
                                        capabilities[key_val] = val_val

            return {"methods": methods, "capabilities": capabilities}

        except Exception as e:
            logger.error(f"Error extracting capabilities from {provider_path}: {e}")
            return {}

    def extract_dependencies(self, plugin_dir: str) -> list[str]:
        """Extract dependencies from requirements.txt.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            List of dependencies
        """
        req_path = os.path.join(plugin_dir, "requirements.txt")
        if not os.path.exists(req_path):
            return []

        try:
            with open(req_path) as f:
                lines = f.readlines()

            # Filter out comments and empty lines
            deps = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    deps.append(line)

            return deps
        except Exception as e:
            logger.error(f"Error extracting dependencies from {req_path}: {e}")
            return []

    def generate_config_schema_docs(self, schema: dict[str, Any]) -> str:
        """Generate documentation for config schema.

        Args:
            schema: Configuration schema

        Returns:
            Markdown documentation
        """
        if not schema or not isinstance(schema, dict) or "properties" not in schema:
            return "No configuration options available."

        properties = schema.get("properties", {})
        if not properties:
            return "No configuration options available."

        docs = "## Configuration Options\n\n"
        docs += "| Option | Type | Description | Default |\n"
        docs += "|--------|------|-------------|--------|\n"

        for name, prop in properties.items():
            prop_type = prop.get("type", "string")
            description = prop.get("description", "No description")
            default = prop.get("default", "None")

            # Format default value based on type
            if isinstance(default, bool):
                default = str(default).lower()
            elif isinstance(default, (list, dict)):
                default = f"`{json.dumps(default)}`"
            elif default is None:
                default = "None"
            else:
                default = f"`{default}`"

            docs += f"| `{name}` | {prop_type} | {description} | {default} |\n"

        return docs

    def generate_examples_docs(self, examples: list[dict[str, Any]]) -> str:
        """Generate documentation for examples.

        Args:
            examples: List of examples

        Returns:
            Markdown documentation
        """
        if not examples:
            return "No examples available."

        docs = "## Examples\n\n"

        for i, example in enumerate(examples):
            name = example.get("name", f"Example {i + 1}")
            description = example.get("description", "No description")

            docs += f"### {name}\n\n"
            docs += f"{description}\n\n"

            # Input
            input_data = example.get("input", {})
            if input_data:
                docs += "**Input:**\n\n"
                docs += "```json\n"
                docs += json.dumps(input_data, indent=2)
                docs += "\n```\n\n"

            # Expected output
            output = example.get("expected_output", {})
            if output:
                docs += "**Expected Output:**\n\n"
                docs += "```json\n"
                docs += json.dumps(output, indent=2)
                docs += "\n```\n\n"

        return docs

    def generate_methods_docs(self, methods: list[dict[str, Any]]) -> str:
        """Generate documentation for provider methods.

        Args:
            methods: List of methods

        Returns:
            Markdown documentation
        """
        if not methods:
            return "No public methods available."

        docs = "## Provider Methods\n\n"

        for method in methods:
            name = method.get("name", "")
            docstring = method.get("docstring", "No description")
            params = method.get("params", [])

            docs += f"### `{name}`\n\n"

            if docstring:
                docs += f"{docstring}\n\n"

            if params:
                docs += "**Parameters:**\n\n"
                for param in params:
                    docs += f"- `{param}`\n"
                docs += "\n"

        return docs

    def generate_plugin_doc(self, plugin_dir: str) -> str:
        """Generate documentation for a plugin.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Markdown documentation
        """
        # Load metadata
        metadata = self.load_plugin_metadata(plugin_dir)
        if not metadata:
            logger.error(f"Failed to load metadata for {plugin_dir}")
            return ""

        # Extract capabilities and methods
        provider_info = self.extract_provider_capabilities(plugin_dir)

        # Extract dependencies
        dependencies = self.extract_dependencies(plugin_dir)

        # Generate plugin path from directory
        rel_path = os.path.relpath(plugin_dir, self.plugins_dir)
        plugin_path = rel_path.replace(os.path.sep, "/")

        # Generate header
        docs = f"# {metadata.get('name', plugin_path)}\n\n"
        docs += f"{metadata.get('description', 'No description')}\n\n"

        # Generate metadata section
        docs += "## Plugin Information\n\n"
        docs += f"- **Version:** {metadata.get('version', '0.1.0')}\n"
        docs += f"- **Author:** {metadata.get('author', 'Unknown')}\n"
        docs += f"- **Plugin Type:** {metadata.get('plugin_type', 'Unknown')}\n"
        docs += f"- **Category:** {metadata.get('category', 'Unknown')}\n"
        docs += f"- **Provider Name:** {metadata.get('provider_name', 'Unknown')}\n"
        docs += "\n"

        # Generate configuration section
        docs += self.generate_config_schema_docs(metadata.get("config_schema", {}))
        docs += "\n"

        # Generate methods section
        docs += self.generate_methods_docs(provider_info.get("methods", []))
        docs += "\n"

        # Generate examples section
        docs += self.generate_examples_docs(metadata.get("examples", []))
        docs += "\n"

        # Generate dependencies section
        if dependencies:
            docs += "## Dependencies\n\n"
            for dep in dependencies:
                docs += f"- `{dep}`\n"

        return docs

    def write_plugin_doc(self, plugin_dir: str, doc_content: str) -> str:
        """Write plugin documentation to a file.

        Args:
            plugin_dir: Path to plugin directory
            doc_content: Documentation content

        Returns:
            Path to the documentation file
        """
        # Generate directory structure
        rel_path = os.path.relpath(plugin_dir, self.plugins_dir)
        doc_dir = os.path.join(self.output_dir, os.path.dirname(rel_path))
        os.makedirs(doc_dir, exist_ok=True)

        # Generate filename
        plugin_name = os.path.basename(plugin_dir)
        doc_path = os.path.join(doc_dir, f"{plugin_name}.md")

        # Write content
        with open(doc_path, "w") as f:
            f.write(doc_content)

        return doc_path

    def generate_index(self, plugin_docs: list[tuple[str, str]]) -> str:
        """Generate index page for all plugins.

        Args:
            plugin_docs: List of (plugin_dir, doc_path) tuples

        Returns:
            Index content
        """
        # Group plugins by domain and category
        domains: dict[str, dict[str, list[tuple[str, str, str]]]] = {}

        for plugin_dir, doc_path in plugin_docs:
            # Load metadata
            metadata = self.load_plugin_metadata(plugin_dir)
            if not metadata:
                continue

            domain = metadata.get("plugin_type", "Unknown")
            category = metadata.get("category", "Other")
            name = metadata.get("name", os.path.basename(plugin_dir))
            description = metadata.get("description", "No description")

            if domain not in domains:
                domains[domain] = {}

            if category not in domains[domain]:
                domains[domain][category] = []

            rel_doc_path = os.path.relpath(doc_path, self.output_dir)
            domains[domain][category].append((name, description, rel_doc_path))

        # Generate index content
        index = "# PepperPy Plugins\n\n"
        index += "This is the documentation for all available plugins in the PepperPy framework.\n\n"

        # Generate table of contents
        index += "## Table of Contents\n\n"

        for domain in sorted(domains.keys()):
            index += f"- [{domain}](#domain-{domain.lower()})\n"
            for category in sorted(domains[domain].keys()):
                index += (
                    f"  - [{category}](#category-{domain.lower()}-{category.lower()})\n"
                )

        index += "\n"

        # Generate domain and category sections
        for domain in sorted(domains.keys()):
            index += f"## Domain: {domain}\n\n"
            index += f'<a id="domain-{domain.lower()}"></a>\n\n'

            for category in sorted(domains[domain].keys()):
                index += f"### Category: {category}\n\n"
                index += (
                    f'<a id="category-{domain.lower()}-{category.lower()}"></a>\n\n'
                )

                # Generate plugin table
                index += "| Plugin | Description |\n"
                index += "|--------|-------------|\n"

                for name, description, doc_path in sorted(domains[domain][category]):
                    index += f"| [{name}]({doc_path}) | {description} |\n"

                index += "\n"

        return index

    def generate_docs(self, plugin_paths: list[str] | None = None) -> list[str]:
        """Generate documentation for plugins.

        Args:
            plugin_paths: Optional list of plugin paths to document

        Returns:
            List of generated documentation files
        """
        # Find plugins if not specified
        if not plugin_paths:
            plugin_paths = self.find_plugins()

        # Generate documentation for each plugin
        doc_files = []
        plugin_docs = []

        for plugin_dir in plugin_paths:
            logger.info(f"Generating documentation for {plugin_dir}")

            doc_content = self.generate_plugin_doc(plugin_dir)
            if doc_content:
                doc_path = self.write_plugin_doc(plugin_dir, doc_content)
                doc_files.append(doc_path)
                plugin_docs.append((plugin_dir, doc_path))

                logger.info(f"Generated documentation: {doc_path}")

        # Generate index
        if doc_files:
            logger.info("Generating index")

            index_content = self.generate_index(plugin_docs)
            index_path = os.path.join(self.output_dir, "index.md")

            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)

            # Write index
            with open(index_path, "w") as f:
                f.write(index_content)

            doc_files.append(index_path)
            logger.info(f"Generated index: {index_path}")

        return doc_files


def main() -> int:
    """Run the documentation generator.

    Returns:
        Exit code (0 for success, non-zero otherwise)
    """
    parser = argparse.ArgumentParser(
        description="Generate documentation for PepperPy plugins"
    )
    parser.add_argument(
        "-d", "--plugins-dir", default="plugins", help="Base plugins directory"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="docs/plugins",
        help="Output directory for documentation",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-s", "--single", help="Generate documentation for a single plugin directory"
    )
    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create generator
    generator = DocGenerator(plugins_dir=args.plugins_dir, output_dir=args.output_dir)

    try:
        if args.single:
            # Generate documentation for a single plugin
            plugin_dir = args.single
            if not os.path.isdir(plugin_dir):
                logger.error(f"Error: {plugin_dir} is not a directory")
                return 1

            doc_files = generator.generate_docs([plugin_dir])
        else:
            # Generate documentation for all plugins
            doc_files = generator.generate_docs()

        if not doc_files:
            logger.warning("No documentation was generated")
            return 1

        print(f"Generated {len(doc_files)} documentation files")
        return 0

    except Exception as e:
        logger.error(f"Error generating documentation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
