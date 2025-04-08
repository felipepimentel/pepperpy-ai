"""
Command-line interface for PepperPy.

This module provides a command-line interface for interacting with PepperPy.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Protocol

from pepperpy.core.errors import PepperpyError
from pepperpy.orchestration import WorkflowOrchestrator
from pepperpy.plugin.discovery import PluginDiscoveryProvider
from pepperpy.plugin.registry import get_registry


# Define a protocol for workflow providers
class WorkflowProviderProtocol(Protocol):
    """Protocol for workflow providers."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def execute(self, input_data: dict[str, Any]) -> Any:
        """Execute workflow with input data."""
        ...


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class CLI:
    """Command-line interface for PepperPy."""

    def __init__(self) -> None:
        """Initialize CLI."""
        self.parser = self._create_parser()
        self.logger = logging.getLogger("pepperpy.cli")
        self._orchestrator = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="PepperPy command-line interface",
            prog="pepperpy",
        )

        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose output"
        )

        # Create subparsers for top-level commands
        subparsers = parser.add_subparsers(
            title="commands", dest="command", help="Command to execute"
        )

        # Plugin commands
        plugin_parser = subparsers.add_parser(
            "plugin",
            help="Manage plugins",
        )
        plugin_subparsers = plugin_parser.add_subparsers(
            title="plugin commands",
            dest="plugin_command",
            help="Plugin command to execute",
        )

        # List plugins
        list_plugins = plugin_subparsers.add_parser(
            "list",
            help="List available plugins",
        )
        list_plugins.add_argument(
            "type",
            nargs="?",
            help="Plugin type to filter",
        )

        # Plugin info
        plugin_info = plugin_subparsers.add_parser(
            "info",
            help="Show plugin information",
        )
        plugin_info.add_argument(
            "plugin_id",
            help="Plugin ID to show info for",
        )

        # Workflow commands
        workflow_parser = subparsers.add_parser(
            "workflow",
            help="Manage workflows",
        )
        workflow_subparsers = workflow_parser.add_subparsers(
            title="workflow commands",
            dest="workflow_command",
            help="Workflow command to execute",
        )

        # List workflows
        list_workflows = workflow_subparsers.add_parser(
            "list",
            help="List available workflows",
        )

        # Info workflow
        info_workflow = workflow_subparsers.add_parser(
            "info",
            help="Show workflow information",
        )
        info_workflow.add_argument(
            "workflow_id",
            help="ID of the workflow to show info for (<type>/<name>)",
        )

        # Run workflow
        run_workflow = workflow_subparsers.add_parser(
            "run",
            help="Run a workflow",
        )
        run_workflow.add_argument(
            "workflow_id",
            help="ID of the workflow to run (<type>/<name>)",
        )
        run_workflow.add_argument(
            "--input",
            type=str,
            help="Input data for the workflow (JSON string or path to JSON file)",
        )
        run_workflow.add_argument(
            "--config",
            type=str,
            help="Configuration for the workflow (JSON string or path to JSON file)",
        )
        run_workflow.add_argument(
            "--params",
            nargs="*",
            help="Additional parameters for the workflow (key=value format)",
        )

        return parser

    @property
    def orchestrator(self) -> WorkflowOrchestrator:
        """Get the workflow orchestrator instance.

        Returns:
            WorkflowOrchestrator instance
        """
        if self._orchestrator is None:
            self._orchestrator = WorkflowOrchestrator()
        return self._orchestrator

    async def _handle_plugin_command(self, args: argparse.Namespace) -> None:
        """Handle plugin-related commands.

        Args:
            args: Parsed command-line arguments
        """
        if args.plugin_command == "list":
            await self._list_plugins(args.type)
        elif args.plugin_command == "info":
            await self._show_plugin_info(args.plugin_id)
        else:
            self.parser.error("Invalid plugin command")

    async def _list_plugins(self, plugin_type: str | None = None) -> None:
        """List available plugins.

        Args:
            plugin_type: Optional plugin type to filter
        """
        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        plugins = get_registry().list_plugins()

        if plugin_type:
            if plugin_type not in plugins:
                print(f"No plugins found for type '{plugin_type}'.")
                return

            print(f"Available {plugin_type} plugins:")
            print("---------------------" + "-" * len(plugin_type))
            for name, plugin_class in sorted(plugins[plugin_type].items()):
                plugin_id = f"{plugin_type}/{name}"
                plugin_info = getattr(plugin_class, "__plugin_info__", {})
                description = plugin_info.get("description", "No description")
                print(f"  - {plugin_id}: {description}")
        else:
            print("Available plugin types:")
            print("---------------------")
            for p_type, p_dict in sorted(plugins.items()):
                print(f"  - {p_type} ({len(p_dict)} plugins)")

    async def _show_plugin_info(self, plugin_id: str) -> None:
        """Show information about a plugin.

        Args:
            plugin_id: Plugin ID (<type>/<name>)
        """
        try:
            plugin_type, plugin_name = plugin_id.split("/", 1)
        except ValueError:
            self.logger.error("Invalid plugin ID format. Use <type>/<name>")
            return

        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        plugins = get_registry().list_plugins()

        if plugin_type not in plugins:
            self.logger.error(f"Plugin type '{plugin_type}' not found")
            return

        if plugin_name not in plugins[plugin_type]:
            self.logger.error(f"Plugin '{plugin_id}' not found")
            return

        plugin_class = plugins[plugin_type][plugin_name]
        plugin_info = getattr(plugin_class, "__plugin_info__", {})

        print(f"Plugin: {plugin_id}")
        print("-" * (len(plugin_id) + 8))
        print(f"Name: {plugin_info.get('name', plugin_id)}")
        print(f"Version: {plugin_info.get('version', 'unknown')}")
        print(f"Description: {plugin_info.get('description', 'No description')}")
        print(f"Author: {plugin_info.get('author', 'unknown')}")
        print()

        if "config_schema" in plugin_info:
            print("Configuration schema:")
            print("---------------------")
            schema = plugin_info["config_schema"]
            if schema.get("properties"):
                for name, prop in schema["properties"].items():
                    default = prop.get("default", "none")
                    required = name in schema.get("required", [])
                    req_str = "(required)" if required else "(optional)"
                    print(f"  - {name} {req_str}: {prop.get('description', '')}")
                    print(f"    Type: {prop.get('type', 'any')}, Default: {default}")
            else:
                print("  No configuration properties defined")
            print()

        if "documentation" in plugin_info:
            print("Documentation:")
            print("--------------")
            print(plugin_info["documentation"])

    async def _handle_workflow_command(self, args: argparse.Namespace) -> None:
        """Handle workflow-related commands.

        Args:
            args: Parsed command-line arguments
        """
        if args.workflow_command == "list":
            await self._list_workflows()
        elif args.workflow_command == "info":
            await self._show_workflow_info(args.workflow_id)
        elif args.workflow_command == "run":
            # Process input data from JSON string or file
            if args.input:
                input_data = self._load_json_data(args.input)
            else:
                input_data = {}

            # Process config from JSON string or file
            if args.config:
                config = self._load_json_data(args.config)
            else:
                config = {}

            # If params are provided via command line, process them
            if hasattr(args, "params") and args.params:
                for param in args.params:
                    if "=" in param:
                        key, value = param.split("=", 1)
                        try:
                            # Try to convert to appropriate type
                            if value.lower() == "true":
                                value = True
                            elif value.lower() == "false":
                                value = False
                            elif value.isdigit():
                                value = int(value)
                            elif (
                                value.replace(".", "", 1).isdigit()
                                and value.count(".") <= 1
                            ):
                                value = float(value)
                        except (ValueError, AttributeError):
                            pass

                        # Add to input data
                        input_data[key] = value

            await self._run_workflow(args.workflow_id, input_data, config)
        else:
            self.parser.error("Invalid workflow command")

    def _load_json_data(self, data_source: str) -> dict[str, Any]:
        """Load JSON data from string or file.

        Args:
            data_source: JSON string or path to JSON file

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            # Try parsing as direct JSON
            return json.loads(data_source)
        except json.JSONDecodeError:
            # Try loading as file path
            try:
                with open(data_source) as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                raise ValueError(f"Invalid JSON data or file: {e}")

    async def _list_workflows(self) -> None:
        """List available workflows."""
        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        plugins = get_registry().list_plugins()

        workflow_plugins = plugins.get("workflow", {})

        if not workflow_plugins:
            print("No workflow plugins found.")
            return

        print("Available Workflows:")
        print("-------------------")

        for name, plugin_class in sorted(workflow_plugins.items()):
            plugin_id = f"workflow/{name}"
            plugin_info = getattr(plugin_class, "__plugin_info__", {})
            description = plugin_info.get("description", "No description")
            print(f"  - {plugin_id}: {description}")

    async def _show_workflow_info(self, workflow_id: str) -> None:
        """Show information about a workflow.

        Args:
            workflow_id: Workflow ID (<type>/<name>)
        """
        try:
            workflow_type, workflow_name = workflow_id.split("/", 1)
        except ValueError:
            self.logger.error("Invalid workflow ID format. Use <type>/<name>")
            return

        if workflow_type != "workflow":
            self.logger.error(f"Invalid workflow type: {workflow_type}")
            return

        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        plugins = get_registry().list_plugins()

        workflow_plugins = plugins.get("workflow", {})

        if workflow_name not in workflow_plugins:
            self.logger.error(f"Workflow '{workflow_id}' not found")
            return

        plugin_class = workflow_plugins[workflow_name]
        plugin_info = getattr(plugin_class, "__plugin_info__", {})

        print(f"Workflow: {workflow_id}")
        print("-" * (len(workflow_id) + 10))
        print(f"Name: {plugin_info.get('name', workflow_id)}")
        print(f"Version: {plugin_info.get('version', 'unknown')}")
        print(f"Description: {plugin_info.get('description', 'No description')}")
        print(f"Author: {plugin_info.get('author', 'unknown')}")
        print()

        if "config_schema" in plugin_info:
            print("Configuration schema:")
            print("---------------------")
            schema = plugin_info["config_schema"]
            if schema.get("properties"):
                for name, prop in schema["properties"].items():
                    default = prop.get("default", "none")
                    required = name in schema.get("required", [])
                    req_str = "(required)" if required else "(optional)"
                    print(f"  - {name} {req_str}: {prop.get('description', '')}")
                    print(f"    Type: {prop.get('type', 'any')}, Default: {default}")
            else:
                print("  No configuration properties defined")
            print()

        if "documentation" in plugin_info:
            print("Documentation:")
            print("--------------")
            print(plugin_info["documentation"])

        if "usage" in plugin_info:
            print("\nUsage examples:")
            print("--------------")
            print(plugin_info["usage"])

    async def _run_workflow(
        self, workflow_id: str, input_data: dict[str, Any], config: dict[str, Any]
    ) -> None:
        """Run a workflow.

        Args:
            workflow_id: Workflow ID (<type>/<n>)
            input_data: Input data for the workflow
            config: Configuration for the workflow
        """
        try:
            workflow_type, workflow_name = workflow_id.split("/", 1)
        except ValueError:
            self.logger.error("Invalid workflow ID format. Use <type>/<n>")
            return

        if workflow_type != "workflow":
            self.logger.error(f"Invalid workflow type: {workflow_type}")
            return

        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        # Import for plugin creation
        from pepperpy.plugin import create_provider_instance

        try:
            print(f"Running workflow: {workflow_id}")
            print("------------------------" + "-" * len(workflow_id))

            # Format input data for workflow execution
            task_input = {
                "task": input_data.pop("task", "default"),
                "input": input_data,
                "options": input_data.pop("options", {}),
            }

            # Debug print of the registry
            registry = get_registry()
            print("DEBUG: Workflow Registry Contents:")
            workflow_plugins = registry._plugins.get("workflow", {})
            print(f"DEBUG: Registry memory ID: {id(registry)}")
            for key in workflow_plugins.keys():
                print(f"  - {key}")

            # Get the workflow provider
            try:
                # Print what we're looking for
                print(
                    f"DEBUG: Looking for provider with domain='workflow', name='{workflow_name}'"
                )
                print(f"DEBUG: Trying alternative name='{workflow_id}'")
                print(f"DEBUG: Also trying name='workflow/{workflow_name}'")

                # Use the protocol to type the provider correctly
                print(f"Trying to create workflow provider: {workflow_name}")

                # Try with just the workflow name first
                try:
                    workflow_provider = create_provider_instance(
                        "workflow", workflow_name, **config
                    )
                except Exception:
                    # If that fails, try with the full path
                    try:
                        workflow_provider = create_provider_instance(
                            "workflow", workflow_id, **config
                        )
                    except Exception:
                        # If that fails too, try with workflow/workflow/ prefix
                        workflow_provider = create_provider_instance(
                            "workflow", f"workflow/{workflow_name}", **config
                        )

                workflow_provider_typed: WorkflowProviderProtocol = workflow_provider  # type: ignore
            except Exception as e:
                self.logger.error(f"Failed to create workflow provider: {e}")
                return

            # Initialize the provider
            await workflow_provider_typed.initialize()

            # Execute the workflow
            try:
                result = await workflow_provider_typed.execute(task_input)

                # Print the result
                if hasattr(result, "to_dict"):
                    print("\nResult:")
                    print(json.dumps(result.to_dict(), indent=2))
                else:
                    print("\nResult:")
                    print(json.dumps(result, indent=2, default=str))
            except Exception as e:
                self.logger.error(f"Failed to execute workflow: {e}")
                return
            finally:
                # Clean up
                await workflow_provider_typed.cleanup()

        except Exception as e:
            self.logger.error(f"Error running workflow: {e}")

    async def run_async(self) -> None:
        """Run CLI asynchronously."""
        args = self.parser.parse_args()

        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        try:
            if args.command == "plugin":
                await self._handle_plugin_command(args)
            elif args.command == "workflow":
                await self._handle_workflow_command(args)
            else:
                self.parser.print_help()
        except PepperpyError as e:
            self.logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            self.logger.exception("Unexpected error: %s", e)
            sys.exit(1)

    def run(self) -> None:
        """Run CLI synchronously."""
        asyncio.run(self.run_async())


def main() -> None:
    """Run CLI main entry point."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
