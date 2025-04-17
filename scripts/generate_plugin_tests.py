#!/usr/bin/env python3
"""
Plugin Test Generator for PepperPy.

This script generates pytest files for plugins based on the examples defined
in plugin.yaml files. It creates tests that validate the functionality
described in the examples.
"""

import argparse
import glob
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


class TestGenerator:
    """Generates pytest files for plugins based on examples."""

    def __init__(
        self,
        plugins_dir: str = "plugins",
        output_dir: str = "tests",
        templates_dir: str = "templates/plugin_tests_template",
    ) -> None:
        """Initialize generator.

        Args:
            plugins_dir: Base directory for plugins
            output_dir: Directory to write tests
            templates_dir: Directory with test templates
        """
        self.plugins_dir = plugins_dir
        self.output_dir = output_dir
        self.templates_dir = templates_dir

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

    def parse_plugin_path(self, plugin_dir: str) -> tuple[str, str, str]:
        """Parse a plugin directory path into domain, category, provider.

        Args:
            plugin_dir: Path to the plugin directory

        Returns:
            Tuple of (domain, category, provider)
        """
        # Get relative path from plugins dir
        rel_path = os.path.relpath(plugin_dir, self.plugins_dir)
        parts = rel_path.split(os.path.sep)

        if len(parts) != 3:
            raise ValueError(
                f"Plugin path must have 3 parts (domain/category/provider), got {len(parts)}: {rel_path}"
            )

        return parts[0], parts[1], parts[2]

    def get_provider_class_name(self, plugin_dir: str) -> str:
        """Get the provider class name from plugin.yaml.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Provider class name
        """
        metadata = self.load_plugin_metadata(plugin_dir)
        if not metadata:
            return ""

        # Get from entry_point
        entry_point = metadata.get("entry_point", "")
        if entry_point:
            # Format is typically module.ClassName or ClassName
            parts = entry_point.split(".")
            return parts[-1]

        # Fall back to capitalizing provider name
        domain, category, provider = self.parse_plugin_path(plugin_dir)
        return "".join(word.capitalize() for word in provider.split("_")) + "Provider"

    def extract_examples(self, plugin_dir: str) -> list[dict[str, Any]]:
        """Extract examples from plugin.yaml.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            List of examples
        """
        metadata = self.load_plugin_metadata(plugin_dir)
        return metadata.get("examples", [])

    def generate_test_for_example(
        self, example: dict[str, Any], provider_class: str, plugin_path: str
    ) -> str:
        """Generate a test function for an example.

        Args:
            example: Example dictionary
            provider_class: Name of the provider class
            plugin_path: Path to the plugin for imports

        Returns:
            Test function code
        """
        name = example.get("name", "").replace(" ", "_").lower()
        if not name:
            name = "unnamed_example"

        description = example.get("description", "No description")
        input_data = example.get("input", {})
        expected_output = example.get("expected_output", {})

        # Generate test function
        test_code = f"""
@pytest.mark.asyncio
async def test_{name}():
    \"\"\"
    Test: {description}
    \"\"\"
    from plugins.{plugin_path}.provider import {provider_class}
    
    # Initialize provider
    provider = {provider_class}()
    await provider.initialize()
    
    try:
        # Prepare input data
        input_data = {input_data}
        
        # Execute provider
        result = await provider.execute(input_data)
        
        # Verify result
        expected = {expected_output}
        
        # Check status
        assert result.get("status") == expected.get("status"), f"Status mismatch: {{result.get('status')}} != {{expected.get('status')}}"
        
        # Check result content
        if "result" in expected:
            assert "result" in result, "Result missing from response"
"""

        # Add specific assertions based on expected output type
        if "result" in expected_output:
            expected_result = expected_output["result"]
            if isinstance(expected_result, dict):
                test_code += "            # Check dictionary result keys\n"
                test_code += "            for key in expected['result']:\n"
                test_code += "                assert key in result['result'], f\"Key {{key}} missing from result\"\n"
            elif isinstance(expected_result, list):
                test_code += "            # Check list result\n"
                test_code += "            assert isinstance(result['result'], list), \"Result should be a list\"\n"
                if expected_result:
                    test_code += "            assert len(result['result']) > 0, \"Result list is empty\"\n"
            else:
                test_code += "            # Check simple result value\n"
                test_code += "            assert result['result'] == expected['result'], f\"Result mismatch: {{result['result']}} != {{expected['result']}}\"\n"

        # Add cleanup
        test_code += """
    finally:
        # Clean up
        await provider.cleanup()
"""

        return test_code

    def generate_test_file(self, plugin_dir: str) -> str:
        """Generate a test file for a plugin based on examples.

        Args:
            plugin_dir: Path to the plugin directory

        Returns:
            Path to the generated test file
        """
        try:
            # Parse plugin information
            domain, category, provider = self.parse_plugin_path(plugin_dir)
            plugin_path = f"{domain}/{category}/{provider}"
            provider_class = self.get_provider_class_name(plugin_dir)

            # Extract examples
            examples = self.extract_examples(plugin_dir)
            if not examples:
                logger.warning(f"No examples found for {plugin_dir}")
                return ""

            # Create test directory
            test_dir = os.path.join(self.output_dir, domain, category, provider)
            os.makedirs(test_dir, exist_ok=True)

            # Generate test file path
            test_file = os.path.join(test_dir, "test_examples.py")

            # Generate file content
            content = f"""#!/usr/bin/env python3
\"\"\"
Auto-generated tests for {plugin_path} plugin.

These tests are generated from examples in plugin.yaml.
\"\"\"

import asyncio
import json
import os
import sys
from typing import Any, Dict

import pytest


"""

            # Add tests for each example
            for example in examples:
                test_function = self.generate_test_for_example(
                    example, provider_class, plugin_path
                )
                content += test_function + "\n"

            # Write test file
            with open(test_file, "w") as f:
                f.write(content)

            logger.info(f"Generated test file: {test_file}")
            return test_file

        except Exception as e:
            logger.error(f"Error generating test file for {plugin_dir}: {e}")
            return ""

    def generate_test_helper(self, plugin_dir: str) -> str:
        """Generate a test helper file for a plugin.

        Args:
            plugin_dir: Path to the plugin directory

        Returns:
            Path to the generated helper file
        """
        try:
            # Parse plugin information
            domain, category, provider = self.parse_plugin_path(plugin_dir)
            plugin_path = f"{domain}/{category}/{provider}"
            provider_class = self.get_provider_class_name(plugin_dir)

            # Create test directory
            test_dir = os.path.join(self.output_dir, domain, category, provider)
            os.makedirs(test_dir, exist_ok=True)

            # Generate test file path
            helper_file = os.path.join(test_dir, "conftest.py")

            # Generate file content
            content = f"""#!/usr/bin/env python3
\"\"\"
Test helpers for {plugin_path} plugin.
\"\"\"

import asyncio
import json
import os
import pytest
from typing import Any, Dict

from plugins.{plugin_path}.provider import {provider_class}


@pytest.fixture
async def provider():
    \"\"\"Fixture for initialized provider.\"\"\"
    provider_instance = {provider_class}()
    await provider_instance.initialize()
    
    yield provider_instance
    
    await provider_instance.cleanup()


def load_test_data(filename: str) -> Dict[str, Any]:
    \"\"\"Load test data from a JSON file.\"\"\"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "data", filename)
    
    with open(data_path, "r") as f:
        return json.load(f)
"""

            # Create data directory for tests
            data_dir = os.path.join(test_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            # Write helper file
            with open(helper_file, "w") as f:
                f.write(content)

            logger.info(f"Generated test helper: {helper_file}")
            return helper_file

        except Exception as e:
            logger.error(f"Error generating test helper for {plugin_dir}: {e}")
            return ""

    def generate_tests(self, plugin_paths: list[str] | None = None) -> list[str]:
        """Generate tests for plugins.

        Args:
            plugin_paths: Optional list of plugin paths to generate tests for

        Returns:
            List of generated test files
        """
        # Find plugins if not specified
        if not plugin_paths:
            plugin_paths = self.find_plugins()

        # Generate tests for each plugin
        generated_files = []

        for plugin_dir in plugin_paths:
            logger.info(f"Generating tests for {plugin_dir}")

            # Generate test file from examples
            test_file = self.generate_test_file(plugin_dir)
            if test_file:
                generated_files.append(test_file)

            # Generate test helper
            helper_file = self.generate_test_helper(plugin_dir)
            if helper_file:
                generated_files.append(helper_file)

        return generated_files


def main() -> int:
    """Run the test generator.

    Returns:
        Exit code (0 for success, non-zero otherwise)
    """
    parser = argparse.ArgumentParser(
        description="Generate tests for PepperPy plugins based on examples"
    )
    parser.add_argument(
        "-d", "--plugins-dir", default="plugins", help="Base plugins directory"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="tests",
        help="Output directory for tests",
    )
    parser.add_argument(
        "-t",
        "--templates-dir",
        default="templates/plugin_tests_template",
        help="Directory with test templates",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-s", "--single", help="Generate tests for a single plugin directory"
    )
    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create generator
    generator = TestGenerator(
        plugins_dir=args.plugins_dir,
        output_dir=args.output_dir,
        templates_dir=args.templates_dir,
    )

    try:
        if args.single:
            # Generate tests for a single plugin
            plugin_dir = args.single
            if not os.path.isdir(plugin_dir):
                logger.error(f"Error: {plugin_dir} is not a directory")
                return 1

            generated_files = generator.generate_tests([plugin_dir])
        else:
            # Generate tests for all plugins
            generated_files = generator.generate_tests()

        if not generated_files:
            logger.warning("No tests were generated")
            return 1

        print(f"Generated {len(generated_files)} test files")
        return 0

    except Exception as e:
        logger.error(f"Error generating tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
