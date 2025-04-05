"""Command-line interface for PepperPy.

This module provides a robust command-line interface for PepperPy,
enabling users to list and run workflows, manage plugins, and more.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from pepperpy.core import PepperpyError
from pepperpy.plugin.discovery import PluginDiscoveryProvider
from pepperpy.plugin.registry import plugin_registry
from pepperpy.workflow.orchestrator import WorkflowOrchestrator


class CLI:
    """Command-line interface for PepperPy."""

    def __init__(self) -> None:
        """Initialize CLI."""
        self.parser = self._create_parser()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._orchestrator = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="PepperPy CLI - Run AI workflows from the command line",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Global options
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose logging",
        )
        parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 0.1.0",
        )

        # Subcommands
        subparsers = parser.add_subparsers(
            title="commands",
            dest="command",
            help="Command to execute",
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
            "--type",
            help="Filter plugins by type",
        )

        # Show plugin info
        info_plugin = plugin_subparsers.add_parser(
            "info",
            help="Show plugin information",
        )
        info_plugin.add_argument(
            "plugin_id",
            help="Plugin ID (<type>/<name>)",
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
            plugin_type: Optional plugin type to filter by
        """
        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        plugins = plugin_registry.list_plugins()

        if not plugins:
            print("No plugins found.")
            return

        print("Available Plugins:")
        print("------------------")

        for domain, providers in sorted(plugins.items()):
            if plugin_type and domain != plugin_type:
                continue

            if not providers:
                continue

            print(f"\n{domain}:")

            for name in sorted(providers.keys()):
                plugin_id = f"{domain}/{name}"
                print(f"  - {plugin_id}")

    async def _show_plugin_info(self, plugin_id: str) -> None:
        """Show plugin information.

        Args:
            plugin_id: Plugin ID (<type>/<name>)
        """
        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        try:
            plugin_type, plugin_name = plugin_id.split("/", 1)
        except ValueError:
            self.logger.error("Invalid plugin ID format. Use <type>/<name>")
            return

        # Get plugins from registry
        plugins = plugin_registry.list_plugins()
        plugin_providers = plugins.get(plugin_type, {})

        if plugin_name not in plugin_providers:
            self.logger.error(f"Plugin not found: {plugin_id}")
            return

        # Get plugin metadata
        plugin_class = plugin_providers[plugin_name]
        plugin_info = getattr(plugin_class, "__plugin_info__", {})

        if not plugin_info:
            self.logger.error(f"No information available for plugin: {plugin_id}")
            return

        print(f"Plugin: {plugin_id}")
        print("-" * (len(plugin_id) + 8))
        print(f"Version: {plugin_info.get('version', 'N/A')}")
        print(f"Description: {plugin_info.get('description', 'N/A')}")
        print(f"Author: {plugin_info.get('author', 'N/A')}")

        if "documentation" in plugin_info:
            print("\nDocumentation:")
            print(plugin_info["documentation"])

        if "config_schema" in plugin_info:
            print("\nConfiguration Schema:")
            for key, value in plugin_info["config_schema"].items():
                print(f"  {key}:")
                print(f"    Description: {value.get('description', 'N/A')}")
                print(f"    Type: {value.get('type', 'N/A')}")
                if "default" in value:
                    print(f"    Default: {value['default']}")

    async def _handle_workflow_command(self, args: argparse.Namespace) -> None:
        """Handle workflow-related commands.

        Args:
            args: Parsed command-line arguments
        """
        if args.workflow_command == "list":
            await self._list_workflows()
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

        plugins = plugin_registry.list_plugins()

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

            # Get the workflow provider
            try:
                workflow_provider = create_provider_instance(
                    "workflow", workflow_name, **config
                )
            except Exception as e:
                self.logger.error(f"Failed to create workflow provider: {e}")
                return

            # Initialize the provider
            await workflow_provider.initialize()

            try:
                # Execute the workflow with the input data
                # Use a generic approach to avoid type checking issues
                if not hasattr(workflow_provider, "execute"):
                    self.logger.error(
                        f"Workflow provider doesn't support execution: {workflow_name}"
                    )
                    return

                execute_method = workflow_provider.execute
                result = await execute_method(task_input)

                # Format and print result
                if result:
                    # Check if the result has a summary
                    if isinstance(result, dict) and "summary" in result:
                        print("\nWorkflow Summary:")
                        print(result["summary"])
                        print("\nFull Results:")

                    # Print full results
                    try:
                        formatted_result = json.dumps(result, indent=2)
                        print(formatted_result)
                    except (TypeError, ValueError):
                        print(result)
                else:
                    print("\nWorkflow completed with no result.")

                print("\nWorkflow execution completed successfully.")
            finally:
                # Clean up provider
                await workflow_provider.cleanup()

        except Exception as e:
            self.logger.error(f"Error running workflow: {e}")
            if hasattr(e, "__cause__") and e.__cause__:
                self.logger.error(f"Caused by: {e.__cause__}")

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
        except NotImplementedError:
            self.logger.error("Command not implemented yet")
            sys.exit(1)
        except PepperpyError as e:
            self.logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if hasattr(e, "__cause__") and e.__cause__:
                self.logger.error(f"Caused by: {e.__cause__}")
            sys.exit(1)

    def run(self) -> None:
        """Run CLI synchronously."""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            sys.exit(130)


if __name__ == "__main__":
    cli = CLI()
    cli.run()
