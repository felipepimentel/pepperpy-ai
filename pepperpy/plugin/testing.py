"""Plugin utilities.

This module provides utilities for running plugins dynamically.
"""

import asyncio
import importlib.util
import json
import os
import sys
from typing import Any

import yaml


class PluginRunner:
    """Runner for executing plugin functionality."""

    @classmethod
    async def run_plugin(
        cls, plugin_path: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Run plugin with given input.

        Args:
            plugin_path: Path to plugin module and class (module.Class) or
                          directory containing plugin.yaml
            input_data: Input data for plugin execution

        Returns:
            Plugin execution result
        """
        provider_class, _ = await cls._resolve_plugin(plugin_path)

        # Create and initialize provider
        provider = provider_class()
        await provider.initialize()

        try:
            # Execute with input data
            return await provider.execute(input_data)
        finally:
            await provider.cleanup()

    @classmethod
    async def _resolve_plugin(
        cls, plugin_path: str
    ) -> tuple[type, dict[str, Any] | None]:
        """Resolve plugin class from path.

        Supports either:
        - Direct module.Class path
        - Directory containing plugin.yaml

        Returns:
            Tuple containing (ProviderClass, config_dict or None)
        """
        # Check if path is a directory (possibly containing plugin.yaml)
        if os.path.isdir(plugin_path):
            yaml_path = os.path.join(plugin_path, "plugin.yaml")
            if not os.path.exists(yaml_path):
                raise ValueError(f"plugin.yaml not found at {yaml_path}")

            with open(yaml_path) as f:
                config = yaml.safe_load(f)

            entry_point = config.get("entry_point")
            if not entry_point:
                raise ValueError(f"No entry_point defined in {yaml_path}")

            provider_file, provider_class_name = entry_point.split(".")
            plugin_type = config.get("plugin_type")
            provider_name = config.get("provider_name")

            if not all([plugin_type, provider_name]):
                raise ValueError(f"Missing plugin_type or provider_name in {yaml_path}")

            # Import provider from plugins directory
            module_path = f"plugins.{plugin_type}.{provider_name}.{provider_file}"

            try:
                spec = importlib.util.find_spec(module_path)
                if spec is None:
                    raise ImportError(f"Module {module_path} not found")

                module = importlib.util.module_from_spec(spec)
                if spec.loader is None:
                    raise ImportError(f"Failed to load module {module_path}")

                spec.loader.exec_module(module)
                provider_class = getattr(module, provider_class_name)
                return provider_class, config
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Failed to import provider: {e}")

        # Assume direct module.Class path
        else:
            # Check if it's a module.Class format
            if "." not in plugin_path:
                raise ValueError(
                    f"Invalid plugin path: {plugin_path}. "
                    "Should be 'module.Class' or path to plugin directory"
                )

            module_path, class_name = plugin_path.rsplit(".", 1)

            try:
                spec = importlib.util.find_spec(module_path)
                if spec is None:
                    raise ImportError(f"Module {module_path} not found")

                module = importlib.util.module_from_spec(spec)
                if spec.loader is None:
                    raise ImportError(f"Failed to load module {module_path}")

                spec.loader.exec_module(module)
                provider_class = getattr(module, class_name)
                return provider_class, None
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Failed to import provider: {e}")


async def run_plugin_cli() -> None:
    """CLI entry point for running plugins."""
    import argparse

    parser = argparse.ArgumentParser(description="Run plugin")
    parser.add_argument(
        "plugin_path",
        help="Plugin path (module.Class) or directory containing plugin.yaml",
    )
    parser.add_argument(
        "--input", "-i", help="JSON input data or path to JSON file", default="{}"
    )
    parser.add_argument(
        "--pretty", "-p", action="store_true", help="Pretty print output"
    )

    args = parser.parse_args()

    try:
        # Check if input is a file path
        if os.path.isfile(args.input):
            with open(args.input) as f:
                input_data = json.load(f)
        else:
            # Try to parse as JSON
            try:
                input_data = json.loads(args.input)
            except json.JSONDecodeError:
                # Not JSON, use as string
                input_data = {"input": args.input}

        # Run plugin
        result = await PluginRunner.run_plugin(args.plugin_path, input_data)

        # Print result
        if args.pretty:
            print(json.dumps(result, indent=2))
        else:
            print(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_plugin_cli())
