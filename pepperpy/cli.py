"""
PepperPy Command Line Interface.

This module provides the main CLI for the PepperPy framework.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, cast

import yaml

from pepperpy.core.base import PepperpyError
from pepperpy.orchestration import WorkflowOrchestrator
from pepperpy.plugin import get_plugin, list_plugins
from pepperpy.plugin.discovery import PluginDiscoveryProvider, load_specific_plugin
from pepperpy.plugin.registry import get_registry
from pepperpy.plugin.testing import PluginRunner


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

        # Agent commands
        agent_parser = subparsers.add_parser(
            "agent",
            help="Manage agents",
        )
        agent_subparsers = agent_parser.add_subparsers(
            title="agent commands",
            dest="agent_command",
            help="Agent command to execute",
        )

        # List agents
        list_agents = agent_subparsers.add_parser(
            "list",
            help="List available agents",
        )

        # Info agent
        info_agent = agent_subparsers.add_parser(
            "info",
            help="Show agent information",
        )
        info_agent.add_argument(
            "agent_id",
            help="ID of the agent to show info for",
        )

        # Run agent
        run_agent = agent_subparsers.add_parser(
            "run",
            help="Run an agent with a specific task",
        )
        run_agent.add_argument(
            "agent_id",
            help="ID of the agent to run",
        )
        run_agent.add_argument(
            "--task",
            "-t",
            required=True,
            help="Task to execute",
        )
        run_agent.add_argument(
            "--model",
            help="Model to use (overrides default)",
        )
        run_agent.add_argument(
            "--config",
            type=str,
            help="Configuration for the agent (JSON string or path to JSON file)",
        )
        run_agent.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty print the output",
        )

        # Test agent
        test_agent = agent_subparsers.add_parser(
            "test",
            help="Test an agent with examples from plugin.yaml",
        )
        test_agent.add_argument(
            "agent_id",
            help="ID of the agent to test",
        )
        test_agent.add_argument(
            "--example",
            help="Name of specific example to run (default: run all examples)",
        )
        test_agent.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty print the output",
        )

        # Chat with agent
        chat_agent = agent_subparsers.add_parser(
            "chat",
            help="Start an interactive chat session with an agent",
        )
        chat_agent.add_argument(
            "agent_id",
            help="ID of the agent to chat with",
        )
        chat_agent.add_argument(
            "--model",
            help="Model to use (overrides default)",
        )
        chat_agent.add_argument(
            "--system",
            help="System prompt to initialize the chat",
        )
        chat_agent.add_argument(
            "--config",
            type=str,
            help="Configuration for the agent (JSON string or path to JSON file)",
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
            help="ID of the workflow to show info for (<type>/<n>)",
        )

        # Run workflow
        run_workflow = workflow_subparsers.add_parser(
            "run",
            help="Run a workflow",
        )
        run_workflow.add_argument(
            "workflow_id",
            help="ID of the workflow to run (name or type/name)",
        )
        run_workflow.add_argument(
            "--topic",
            "-t",
            help="Topic or main input for the workflow",
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
        run_workflow.add_argument(
            "--output",
            "-o",
            help="Output file for the result (JSON format)",
        )
        run_workflow.add_argument(
            "--task",
            default="default",
            help="Task to execute within the workflow (defaults to 'default')",
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

            # If topic is provided, add it to the input
            if hasattr(args, "topic") and args.topic:
                input_data["topic"] = args.topic

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
                        self.logger.debug(f"Added parameter: {key}={value}")

            # Get output file if specified
            output_file = getattr(args, "output", None)

            # Get task name if specified
            task_name = getattr(args, "task", "default")

            await self._run_workflow(
                args.workflow_id,
                input_data,
                config,
                output_file=output_file,
                task_name=task_name,
            )
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

        # Get the registry to access both loaded plugins and plugin info
        registry = get_registry()

        # Access the plugin info directly from the registry for unloaded plugins
        plugin_infos = registry._plugin_info.get("workflow", {})

        if not plugin_infos:
            print("No workflow plugins found.")
            return

        print("Available Workflows:")
        print("-------------------")

        # Filter out duplicates and ensure consistent naming
        unique_workflows = {}
        for name, plugin_info in plugin_infos.items():
            # Standardize the workflow ID format
            if "/" in name:
                # Already has domain prefix
                parts = name.split("/", 1)
                if parts[0] == "workflow":
                    # Use the name without the workflow/ prefix for display
                    workflow_id = parts[1]
                else:
                    # Keep other prefixes as is
                    workflow_id = name
            else:
                # No prefix, use as is
                workflow_id = name

            # Skip duplicates and prefer the version without prefix
            if name.startswith("workflow/") and name[9:] in unique_workflows:
                continue

            unique_workflows[workflow_id] = plugin_info

        # Display workflows sorted by name
        for workflow_id, plugin_info in sorted(unique_workflows.items()):
            description = plugin_info.description
            print(f"  - {workflow_id}: {description}")

    async def _show_workflow_info(self, workflow_id: str) -> None:
        """Show information about a workflow.

        Args:
            workflow_id: Workflow ID (name or type/name)
        """
        # Normalize workflow_id to ensure it has the proper prefix
        if "/" in workflow_id:
            parts = workflow_id.split("/", 1)
            if parts[0] != "workflow":
                # If it has a different prefix, add workflow prefix
                workflow_type, workflow_name = "workflow", workflow_id
            else:
                # Already has workflow/ prefix
                workflow_type, workflow_name = parts
        else:
            # No prefix, assume it's a workflow name
            workflow_type = "workflow"
            workflow_name = workflow_id

        # Initialize plugin discovery
        discovery = PluginDiscoveryProvider()
        discovery.config = {"scan_paths": [str(Path.cwd() / "plugins")]}

        # Discover plugins
        await discovery.discover_plugins()

        # Get registry to access plugin info for lazy-loaded plugins
        registry = get_registry()

        # Try to find the plugin info in the registry
        plugin_info = None
        full_id = f"{workflow_type}/{workflow_name}"
        if full_id in registry._plugin_info.get("workflow", {}):
            plugin_info = registry._plugin_info["workflow"][full_id]
        elif workflow_name in registry._plugin_info.get("workflow", {}):
            plugin_info = registry._plugin_info["workflow"][workflow_name]

        if not plugin_info:
            self.logger.error(f"Workflow '{workflow_id}' not found")
            return

        # Load the plugin.yaml file for additional information
        plugin_yaml_data = {}
        if plugin_info.module_path:
            plugin_dir = os.path.dirname(plugin_info.module_path)
            yaml_path = os.path.join(plugin_dir, "plugin.yaml")
            if os.path.exists(yaml_path):
                try:
                    with open(yaml_path) as f:
                        plugin_yaml_data = yaml.safe_load(f)
                except Exception as e:
                    self.logger.warning(f"Error loading plugin.yaml: {e}")

        print(f"Workflow: {workflow_id}")
        print("-" * (len(workflow_id) + 10))
        print(f"Name: {plugin_info.name}")
        print(f"Version: {plugin_info.version}")
        print(f"Description: {plugin_info.description}")
        print(f"Author: {plugin_yaml_data.get('author', 'unknown')}")
        print()

        if "config_schema" in plugin_yaml_data:
            print("Configuration schema:")
            print("---------------------")
            schema = plugin_yaml_data["config_schema"]
            for name, props in schema.items():
                required = props.get("required", False)
                req_str = "(required)" if required else "(optional)"
                print(f"  - {name} {req_str}: {props.get('description', '')}")
                print(
                    f"    Type: {props.get('type', 'any')}, Default: {props.get('default', 'none')}"
                )
            print()

        if "documentation" in plugin_yaml_data:
            print("Documentation:")
            print("--------------")
            print(plugin_yaml_data["documentation"])

    async def _run_workflow(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
        config: dict[str, Any],
        output_file: str | None = None,
        task_name: str = "default",
    ) -> None:
        """Run a workflow.

        Args:
            workflow_id: ID of the workflow to run
            input_data: Input data for the workflow
            config: Configuration for the workflow
            output_file: Path to write the output to (if specified)
            task_name: Name of the task to execute (defaults to "default")
        """
        try:
            # Normalize workflow_id to ensure it has the proper prefix
            if "/" in workflow_id:
                parts = workflow_id.split("/", 1)
                if parts[0] != "workflow":
                    # If it has a different prefix, use it as is
                    workflow_type, workflow_name = parts
                else:
                    # Already has workflow/ prefix
                    workflow_type, workflow_name = parts
            else:
                # No prefix, assume it's a workflow name
                workflow_type = "workflow"
                workflow_name = workflow_id

            # Structure the task input format
            task_input: dict[str, Any] = {
                "task": task_name,
            }

            # Either directly use the topic (if provided) or include all options
            if "topic" in input_data:
                task_input["topic"] = input_data["topic"]
                # Also add remaining options if any exist
                remaining_options = {
                    k: v for k, v in input_data.items() if k != "topic"
                }
                if remaining_options:
                    task_input["options"] = remaining_options
            else:
                # No topic specified, include all input data as options
                task_input["options"] = input_data

            # Load the workflow plugin
            workflow_provider = await load_specific_plugin(workflow_type, workflow_name)

            if not workflow_provider:
                self.logger.error(f"Workflow not found: {workflow_id}")
                return

            self.logger.info(f"Running workflow: {workflow_id}")
            workflow_provider_typed: WorkflowProviderProtocol = workflow_provider(
                **config
            )  # type: ignore

            # Initialize the provider
            await workflow_provider_typed.initialize()

            # Execute the workflow
            try:
                result = await workflow_provider_typed.execute(task_input)

                # Save result to file if requested
                if output_file:
                    # Convert to dict if needed
                    if hasattr(result, "to_dict"):
                        result_dict = result.to_dict()
                    else:
                        result_dict = result

                    with open(output_file, "w") as f:
                        json.dump(result_dict, f, indent=2, default=str)
                    self.logger.info(f"Result saved to: {output_file}")

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

    async def _handle_agent_command(self, args: argparse.Namespace) -> None:
        """Handle agent-related commands.

        Args:
            args: Parsed command-line arguments
        """
        if args.agent_command == "list":
            await self._handle_agent_list()
        elif args.agent_command == "info":
            await self._handle_agent_info(args.agent_id)
        elif args.agent_command == "run":
            await self._handle_agent_run(args)
        elif args.agent_command == "test":
            await self._handle_agent_test(args)
        elif args.agent_command == "chat":
            await self._handle_agent_chat(args)
        else:
            self.parser.error(f"Unknown agent command: {args.agent_command}")

    async def _handle_agent_list(self) -> None:
        """List available agent plugins."""
        self.logger.info("Available agent plugins:")

        agents = list_plugins("agent")
        if not agents:
            self.logger.info("No agent plugins found")
            return

        # Format and display the list
        for agent in agents:
            if isinstance(agent, dict):
                plugin_type = agent.get("plugin_type", "agent")
                provider_name = agent.get("provider_name", "unknown")
                description = agent.get("description", "No description")
                self.logger.info(f"  {plugin_type}/{provider_name} - {description}")

    async def _handle_agent_info(self, agent_id: str) -> None:
        """Show information about an agent plugin.

        Args:
            agent_id: Agent identifier (type/name)
        """
        if "/" not in agent_id:
            self.logger.error(
                f"Invalid agent ID format: {agent_id}. Use 'type/name' format."
            )
            return

        plugin_type, provider_name = agent_id.split("/", 1)
        if plugin_type != "agent":
            plugin_type = "agent"

        self.logger.info(f"Info for agent: {plugin_type}/{provider_name}")

        # Get plugin metadata
        metadata = get_plugin(plugin_type, provider_name)
        if not metadata:
            self.logger.error(f"Agent not found: {plugin_type}/{provider_name}")
            return

        # Garantir que metadata é um dicionário
        metadata_dict = cast(dict[str, Any], metadata)

        # Display detailed information
        self.logger.info(f"  Name: {metadata_dict.get('name', 'N/A')}")
        self.logger.info(f"  Description: {metadata_dict.get('description', 'N/A')}")
        self.logger.info(f"  Version: {metadata_dict.get('version', 'N/A')}")
        self.logger.info(f"  Author: {metadata_dict.get('author', 'N/A')}")

        # Display configuration schema if available
        config_schema = metadata_dict.get("config_schema", {})
        if config_schema:
            self.logger.info("  Configuration options:")
            for prop_name, prop_info in config_schema.get("properties", {}).items():
                default = prop_info.get("default", "None")
                self.logger.info(
                    f"    {prop_name}: {prop_info.get('description', 'No description')} (default: {default})"
                )

    async def _handle_agent_run(self, args: argparse.Namespace) -> None:
        """Run an agent with a specific task.

        Args:
            args: Command-line arguments
        """
        agent_id = args.agent_id
        if "/" not in agent_id:
            self.logger.error(
                f"Invalid agent ID format: {agent_id}. Use 'type/name' format."
            )
            return

        # Parse configuration
        config = self._parse_json_arg(args.config) if args.config else {}

        # Add model if specified
        if args.model:
            config["model"] = args.model

        # Prepare task input
        task_input = {"task": args.task, "config": config}

        self.logger.info(f"Running agent {agent_id} with task: {args.task}")

        try:
            # Use PluginRunner to execute the agent
            agent_type, agent_name = agent_id.split("/", 1)
            plugin_path = f"plugins/{agent_type}/{agent_name}"

            result = await PluginRunner.run_plugin(plugin_path, task_input)

            # Display the result
            if args.pretty:
                print(json.dumps(result, indent=2))
            else:
                print(result)

        except Exception as e:
            self.logger.error(f"Error running agent: {e}")
            sys.exit(1)

    async def _handle_agent_test(self, args: argparse.Namespace) -> None:
        """Test an agent with examples from plugin.yaml.

        Args:
            args: Command-line arguments
        """
        agent_id = args.agent_id
        if "/" not in agent_id:
            self.logger.error(
                f"Invalid agent ID format: {agent_id}. Use 'type/name' format."
            )
            return

        agent_type, agent_name = agent_id.split("/", 1)
        plugin_path = f"plugins/{agent_type}/{agent_name}"

        # Check if plugin.yaml exists and has examples
        plugin_yaml_path = os.path.join(plugin_path, "plugin.yaml")
        if not os.path.exists(plugin_yaml_path):
            self.logger.error(f"Plugin configuration not found: {plugin_yaml_path}")
            return

        try:
            with open(plugin_yaml_path) as f:
                plugin_config = yaml.safe_load(f)

            examples = plugin_config.get("examples", [])
            if not examples:
                self.logger.error(f"No examples found in {plugin_yaml_path}")
                return

            # Filter by example name if specified
            if args.example:
                examples = [ex for ex in examples if ex.get("name") == args.example]
                if not examples:
                    self.logger.error(
                        f"Example '{args.example}' not found in {plugin_yaml_path}"
                    )
                    return

            self.logger.info(f"Running {len(examples)} example(s) for agent {agent_id}")

            for i, example in enumerate(examples):
                name = example.get("name", f"Example {i + 1}")
                description = example.get("description", "No description")
                input_data = example.get("input", {})
                expected = example.get("expected_output", {})

                self.logger.info(f"  Running example '{name}': {description}")

                # Run the example
                result = await PluginRunner.run_plugin(plugin_path, input_data)

                # Check if result matches expected output
                all_matched = True
                for key, value in expected.items():
                    if key not in result or result[key] != value:
                        all_matched = False
                        self.logger.warning(
                            f"    Expected {key}={value}, got {result.get(key, 'missing')}"
                        )

                if all_matched:
                    self.logger.info("    ✓ Test passed")
                else:
                    self.logger.warning("    ✗ Test failed")

                # Display the result
                if args.pretty:
                    print(json.dumps(result, indent=2))

        except Exception as e:
            self.logger.error(f"Error testing agent: {e}")
            sys.exit(1)

    async def _handle_agent_chat(self, args: argparse.Namespace) -> None:
        """Start an interactive chat session with an agent.

        Args:
            args: Command-line arguments
        """
        agent_id = args.agent_id
        if "/" not in agent_id:
            self.logger.error(
                f"Invalid agent ID format: {agent_id}. Use 'type/name' format."
            )
            return

        # Parse configuration
        config = self._parse_json_arg(args.config) if args.config else {}

        # Add model if specified
        if args.model:
            config["model"] = args.model

        # Prepare for chat session
        agent_type, agent_name = agent_id.split("/", 1)
        plugin_path = f"plugins/{agent_type}/{agent_name}"

        self.logger.info(f"Starting chat session with agent {agent_id}")
        self.logger.info("Type 'exit' or 'quit' to end the session")

        try:
            # Initialize agent
            agent_instance = await self._create_agent_instance(plugin_path, config)

            # Add system message if provided
            messages = []
            if args.system:
                messages.append({"role": "system", "content": args.system})

            # Start interactive loop
            while True:
                # Get user input
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    break

                # Add to messages
                messages.append({"role": "user", "content": user_input})

                # Prepare task input with conversation history
                task_input = {"task": "chat", "messages": messages, "config": config}

                # Send to agent
                print("\nAgent is thinking...")
                result = await agent_instance.execute(task_input)

                # Extract and display response
                response = result.get("response", result.get("content", "No response"))
                print(f"\nAgent: {response}")

                # Add to messages
                messages.append({"role": "assistant", "content": response})

        except Exception as e:
            self.logger.error(f"Error in chat session: {e}")
            return

    async def _create_agent_instance(self, plugin_path: str, config: dict) -> Any:
        """Create and initialize an agent instance.

        Args:
            plugin_path: Path to the plugin
            config: Agent configuration

        Returns:
            Initialized agent instance
        """
        provider_class, plugin_config = await PluginRunner._resolve_plugin(plugin_path)

        # Merge configurations
        if plugin_config:
            config = {**plugin_config, **config}

        # Create instance
        instance = provider_class(**config)

        # Initialize
        await instance.initialize()

        return instance

    def _parse_json_arg(self, arg: str) -> dict[str, Any]:
        """Parse a JSON argument from string or file.

        Args:
            arg: JSON string or path to JSON file

        Returns:
            Parsed JSON as dictionary
        """
        if os.path.isfile(arg):
            with open(arg) as f:
                return json.load(f)
        else:
            try:
                return json.loads(arg)
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON: {arg}")
                return {}

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
            elif args.command == "agent":
                await self._handle_agent_command(args)
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
