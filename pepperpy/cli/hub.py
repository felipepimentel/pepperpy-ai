"""CLI commands for managing local artifacts in the Pepper Hub.

This module provides commands for managing artifacts (prompts, agents, workflows)
in the local Pepper Hub, including pushing, pulling, listing, and executing.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, cast

import click
import yaml
from pydantic import SecretStr

from pepperpy.cli import CommandGroup, logger
from pepperpy.core.errors import ValidationError
from pepperpy.hub import Hub
from pepperpy.hub.agents.base import AgentConfig
from pepperpy.memory import MemoryManager
from pepperpy.monitoring import metrics
from pepperpy.providers import get_provider
from pepperpy.providers.base import Provider, ProviderConfig
from pepperpy.search import VectorStore

# Default hub directory in user's home
HUB_DIR = Path.home() / ".pepper_hub"


def ensure_hub_structure() -> None:
    """Ensure the hub directory structure exists."""
    HUB_DIR.mkdir(exist_ok=True)
    for artifact_type in [
        "prompts",
        "agents",
        "workflows",
        "plugins",
        "chains",
        "memory",
    ]:
        (HUB_DIR / artifact_type).mkdir(exist_ok=True)


class HubCommands(CommandGroup):
    """Hub-related CLI commands."""

    name = "hub"
    help = "Manage local Pepper Hub artifacts (prompts, agents, workflows)"

    @classmethod
    def get_command_group(cls) -> click.Group:
        """Get the hub command group.

        Returns
        -------
            click.Group: The hub command group.

        """

        @click.group(name=cls.name, help=cls.help)
        def hub():
            """Manage local Pepper Hub artifacts."""
            ensure_hub_structure()

        # Add all commands
        hub.add_command(cls.push)
        hub.add_command(cls.pull)
        hub.add_command(cls.list)
        hub.add_command(cls.show)
        hub.add_command(cls.versions)
        hub.add_command(cls.remove)
        hub.add_command(cls.run_agent)
        hub.add_command(cls.run_workflow)
        hub.add_command(cls.validate)

        # New commands
        hub.add_command(cls.export_bundle)
        hub.add_command(cls.import_bundle)
        hub.add_command(cls.search)
        hub.add_command(cls.stats)
        hub.add_command(cls.chain)
        hub.add_command(cls.memory)
        hub.add_command(cls.plugin)
        hub.add_command(cls.test)
        hub.add_command(cls.docs)

        return hub

    @staticmethod
    @click.command()
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    @click.option(
        "-f",
        "--file",
        "file_path",
        type=click.Path(exists=True),
        required=True,
        help="Path to the artifact file",
    )
    def push(artifact_type: str, file_path: str) -> None:
        """Push (add/update) an artifact into the local pepper hub.

        The file must contain 'name', 'type', and 'version'.
        """
        try:
            # Read the file content
            file_ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, "r", encoding="utf-8") as f:
                if file_ext in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif file_ext == ".json":
                    data = json.load(f)
                else:
                    raise ValidationError(
                        "Unsupported file extension. Please use YAML or JSON."
                    )

            # Validate minimal fields
            name = data.get("name")
            version = data.get("version")
            if not name or not version:
                raise ValidationError(
                    "Artifact file must contain 'name' and 'version'."
                )

            # Build path
            artifact_dir = HUB_DIR / f"{artifact_type}s" / name
            artifact_dir.mkdir(parents=True, exist_ok=True)

            # Save as YAML for consistency
            target_file = artifact_dir / f"{version}.yaml"
            with open(target_file, "w", encoding="utf-8") as out:
                yaml.dump(data, out, sort_keys=False)

            logger.info(
                "Artifact pushed successfully",
                name=name,
                version=version,
                type=artifact_type,
            )
            click.echo(
                f"Artifact '{name}' version '{version}' pushed to local hub ({artifact_type}s)."
            )

        except Exception as e:
            logger.error(
                "Failed to push artifact",
                error=str(e),
                file=file_path,
                type=artifact_type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("artifact_type", required=False)
    def list(artifact_type: Optional[str]) -> None:
        """List artifacts in the local hub (optionally filtered by type)."""
        try:
            # Show all types if not specified
            base_path = HUB_DIR
            types_to_check = []
            if artifact_type:
                types_to_check.append(f"{artifact_type}s")
            else:
                types_to_check = ["prompts", "agents", "workflows"]

            for t in types_to_check:
                type_path = base_path / t
                if not type_path.exists():
                    continue
                artifact_names = sorted(
                    [d for d in os.listdir(type_path) if (type_path / d).is_dir()]
                )
                click.echo(f"{t}:")
                for art_name in artifact_names:
                    art_dir = type_path / art_name
                    versions = sorted(
                        [
                            v.replace(".yaml", "")
                            for v in os.listdir(art_dir)
                            if v.endswith(".yaml")
                        ]
                    )
                    latest = versions[-1] if versions else "no versions"
                    click.echo(f"  - {art_name} (latest: {latest})")

            click.echo()  # Empty line for readability

        except Exception as e:
            logger.error(
                "Failed to list artifacts",
                error=str(e),
                type=artifact_type,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    @click.argument("artifact_name")
    @click.option(
        "--version", "-v", default=None, help="Specify artifact version to show."
    )
    def show(artifact_type: str, artifact_name: str, version: Optional[str]) -> None:
        """Display the YAML content of an artifact in the local hub.

        If no version is specified, shows the latest version.
        """
        try:
            art_dir = HUB_DIR / f"{artifact_type}s" / artifact_name
            if not art_dir.exists():
                raise ValidationError("Artifact not found.")

            all_versions = sorted(
                [f for f in os.listdir(art_dir) if f.endswith(".yaml")]
            )
            if not all_versions:
                raise ValidationError("No versions available for this artifact.")

            if version:
                target_file = f"{version}.yaml"
                if target_file not in all_versions:
                    raise ValidationError(f"Version '{version}' not found.")
            else:
                # Use latest
                target_file = all_versions[-1]

            path_to_show = art_dir / target_file
            with open(path_to_show, "r", encoding="utf-8") as f:
                content = f.read()

            click.echo(content)

        except Exception as e:
            logger.error(
                "Failed to show artifact",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    @click.argument("artifact_name")
    @click.option(
        "--version", "-v", default=None, help="List a specific version or all versions."
    )
    def versions(
        artifact_type: str, artifact_name: str, version: Optional[str]
    ) -> None:
        """List available versions of an artifact. Or details of one version."""
        try:
            art_dir = HUB_DIR / f"{artifact_type}s" / artifact_name
            if not art_dir.exists():
                raise ValidationError("Artifact not found.")

            all_files = sorted([f for f in os.listdir(art_dir) if f.endswith(".yaml")])
            if not all_files:
                raise ValidationError("No versions available.")

            all_vers = [f.replace(".yaml", "") for f in all_files]

            if version:
                if version in all_vers:
                    click.echo(f"Artifact '{artifact_name}' has version '{version}'")
                else:
                    raise ValidationError(f"Version '{version}' not found.")
            else:
                click.echo(f"Versions for '{artifact_name}':")
                for v in all_vers:
                    click.echo(f"  - {v}")

        except Exception as e:
            logger.error(
                "Failed to list versions",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    @click.argument("artifact_name")
    @click.option("--version", "-v", default=None, help="Optional version to remove.")
    def remove(artifact_type: str, artifact_name: str, version: Optional[str]) -> None:
        """Remove an artifact or a specific version of it from the local hub."""
        try:
            art_dir = HUB_DIR / f"{artifact_type}s" / artifact_name
            if not art_dir.exists():
                raise ValidationError("Artifact not found.")

            if version:
                target_file = art_dir / f"{version}.yaml"
                if not target_file.exists():
                    raise ValidationError(f"Version '{version}' not found.")
                os.remove(target_file)
                logger.info(
                    "Artifact version removed",
                    type=artifact_type,
                    name=artifact_name,
                    version=version,
                )
                click.echo(f"Removed version '{version}' of '{artifact_name}'.")
                # If directory is empty, optionally remove the entire artifact folder
                if not any(art_dir.iterdir()):
                    shutil.rmtree(art_dir)
                    click.echo("No more versions left, artifact folder removed.")
            else:
                # remove entire artifact folder
                shutil.rmtree(art_dir)
                logger.info(
                    "Artifact removed",
                    type=artifact_type,
                    name=artifact_name,
                )
                click.echo(f"Removed artifact '{artifact_name}' and all its versions.")

        except Exception as e:
            logger.error(
                "Failed to remove artifact",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    @click.argument("artifact_name")
    @click.option(
        "--version", "-v", default=None, help="Specify artifact version to pull."
    )
    @click.option(
        "-o",
        "--output",
        "output_path",
        type=click.Path(),
        required=True,
        help="Output file path",
    )
    def pull(
        artifact_type: str, artifact_name: str, version: Optional[str], output_path: str
    ) -> None:
        """Pull (export) an artifact from the local hub to a file."""
        try:
            art_dir = HUB_DIR / f"{artifact_type}s" / artifact_name
            if not art_dir.exists():
                raise ValidationError("Artifact not found.")

            all_versions = sorted(
                [f for f in os.listdir(art_dir) if f.endswith(".yaml")]
            )
            if not all_versions:
                raise ValidationError("No versions available for this artifact.")

            if version:
                target_file = f"{version}.yaml"
                if target_file not in all_versions:
                    raise ValidationError(f"Version '{version}' not found.")
            else:
                # Use latest
                target_file = all_versions[-1]

            # Copy the file
            source_path = art_dir / target_file
            shutil.copy2(source_path, output_path)

            logger.info(
                "Artifact pulled successfully",
                type=artifact_type,
                name=artifact_name,
                version=version or target_file.replace(".yaml", ""),
                output=output_path,
            )
            click.echo(f"Artifact '{artifact_name}' pulled to '{output_path}'.")

        except Exception as e:
            logger.error(
                "Failed to pull artifact",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                version=version,
                output=output_path,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("agent_name")
    @click.option("--version", "-v", default=None, help="Agent version to run")
    @click.option("--provider", "-p", default="openrouter", help="Provider to use")
    @click.option("--model", "-m", default="openai/gpt-4o-mini", help="Model to use")
    @click.option("--temperature", "-t", default=0.7, help="Temperature for generation")
    @click.option("--max-tokens", default=1000, help="Maximum tokens for generation")
    @click.option(
        "--api-key", envvar="PEPPERPY_API_KEY", help="API key for the provider"
    )
    def run_agent(
        agent_name: str,
        version: Optional[str],
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int,
        api_key: str,
    ) -> None:
        """Run an agent from the hub.

        This command allows you to run an agent directly from the hub.
        The agent must be properly configured in the hub.
        """
        try:
            # Initialize hub
            hub = Hub(storage_dir=HUB_DIR)

            # Load agent configuration
            agent_config = hub.load_artifact("agents", agent_name, version)

            # Create provider config
            provider_config = ProviderConfig(
                provider_type=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=SecretStr(api_key),
            )

            # Initialize provider
            provider_instance = get_provider(
                provider_config.provider_type, provider_config
            )

            # Create agent config
            config = AgentConfig(
                provider=cast(Provider, provider_instance),
                parameters=agent_config,
            )

            # Import and create agent dynamically
            agent_module = __import__(
                f"pepperpy.hub.agents.{agent_name}", fromlist=["Agent"]
            )
            agent_class = agent_module.Agent
            agent = agent_class(config)

            # Run the agent
            click.echo(f"Running agent '{agent_name}'...")
            # TODO: Implement agent execution logic

        except Exception as e:
            logger.error(
                "Failed to run agent",
                error=str(e),
                agent=agent_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("workflow_name")
    @click.option("--version", "-v", default=None, help="Workflow version to run")
    @click.option(
        "--inputs",
        "-i",
        type=click.Path(exists=True),
        help="JSON file with workflow inputs",
    )
    def run_workflow(
        workflow_name: str, version: Optional[str], inputs: Optional[str]
    ) -> None:
        """Run a workflow from the hub.

        This command allows you to run a workflow directly from the hub.
        The workflow and its dependencies must be properly configured.
        """
        try:
            # Initialize hub
            hub = Hub(storage_dir=HUB_DIR)

            # Load workflow configuration
            workflow_config = hub.load_artifact("workflows", workflow_name, version)

            # Load inputs if provided
            workflow_inputs: Dict[str, Any] = {}
            if inputs:
                with open(inputs, "r", encoding="utf-8") as f:
                    workflow_inputs = json.load(f)

            # TODO: Implement workflow execution logic
            click.echo(f"Running workflow '{workflow_name}'...")

        except Exception as e:
            logger.error(
                "Failed to run workflow",
                error=str(e),
                workflow=workflow_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    @click.argument("artifact_name")
    @click.option("--version", "-v", default=None, help="Version to validate")
    def validate(
        artifact_type: str, artifact_name: str, version: Optional[str]
    ) -> None:
        """Validate an artifact's configuration and dependencies.

        This command checks if an artifact is properly configured and
        all its dependencies are available in the hub.
        """
        try:
            # Initialize hub
            hub = Hub(storage_dir=HUB_DIR)

            # Load artifact configuration
            config = hub.load_artifact(f"{artifact_type}s", artifact_name, version)

            # Validate configuration based on type
            if artifact_type == "agent":
                # Check required fields
                required_fields = ["name", "type", "version", "description"]
                for field in required_fields:
                    if field not in config:
                        raise ValidationError(f"Missing required field: {field}")

                # Check provider configuration
                if "provider" in config and not isinstance(config["provider"], dict):
                    raise ValidationError("Invalid provider configuration")

            elif artifact_type == "workflow":
                # Check required fields
                required_fields = ["name", "description", "steps", "inputs", "outputs"]
                for field in required_fields:
                    if field not in config:
                        raise ValidationError(f"Missing required field: {field}")

                # Check steps configuration
                if not isinstance(config["steps"], list):
                    raise ValidationError("Steps must be a list")

                # Validate each step
                for step in config["steps"]:
                    if not isinstance(step, dict):
                        raise ValidationError("Invalid step configuration")
                    if "agent" not in step or "prompt" not in step:
                        raise ValidationError("Steps must have agent and prompt")

            elif artifact_type == "prompt":
                # Check required fields
                required_fields = ["name", "description", "template"]
                for field in required_fields:
                    if field not in config:
                        raise ValidationError(f"Missing required field: {field}")

            click.echo(f"Artifact '{artifact_name}' is valid.")

        except Exception as e:
            logger.error(
                "Validation failed",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("output_path", type=click.Path())
    @click.option(
        "--include-types", "-i", multiple=True, help="Artifact types to include"
    )
    @click.option(
        "--exclude-types", "-e", multiple=True, help="Artifact types to exclude"
    )
    def export_bundle(
        output_path: str,
        include_types: tuple[str, ...],
        exclude_types: tuple[str, ...],
    ) -> None:
        """Export a bundle of artifacts for sharing or backup.

        This command creates a portable bundle containing selected artifacts
        that can be imported into another Pepper Hub instance.
        """
        try:
            # Initialize hub
            hub = Hub(storage_dir=HUB_DIR)

            # Determine types to export
            all_types = {"prompts", "agents", "workflows", "plugins", "chains"}
            types_to_export = set(include_types) if include_types else all_types
            types_to_export -= set(exclude_types)

            bundle = {
                "metadata": {
                    "version": "1.0.0",
                    "exported_at": str(datetime.now()),
                    "types": list(types_to_export),
                },
                "artifacts": {},
            }

            # Export each type
            for artifact_type in types_to_export:
                bundle["artifacts"][artifact_type] = hub.export_artifacts(artifact_type)

            # Save bundle
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, indent=2)

            logger.info(
                "Bundle exported successfully",
                path=output_path,
                types=list(types_to_export),
            )
            click.echo(f"Bundle exported to '{output_path}'")

        except Exception as e:
            logger.error(
                "Failed to export bundle",
                error=str(e),
                path=output_path,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("bundle_path", type=click.Path(exists=True))
    @click.option(
        "--dry-run",
        is_flag=True,
        help="Show what would be imported without making changes",
    )
    def import_bundle(bundle_path: str, dry_run: bool) -> None:
        """Import a bundle of artifacts into the local hub.

        This command imports artifacts from a bundle created by export-bundle.
        Use --dry-run to preview the changes without applying them.
        """
        try:
            # Load bundle
            with open(bundle_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)

            # Validate bundle format
            if "metadata" not in bundle or "artifacts" not in bundle:
                raise ValidationError("Invalid bundle format")

            # Initialize hub
            hub = Hub(storage_dir=HUB_DIR)

            # Preview or import
            for artifact_type, artifacts in bundle["artifacts"].items():
                if dry_run:
                    click.echo(f"\nWould import {len(artifacts)} {artifact_type}:")
                    for art in artifacts:
                        click.echo(f"  - {art['name']} (v{art['version']})")
                else:
                    hub.import_artifacts(artifact_type, artifacts)

            if not dry_run:
                logger.info(
                    "Bundle imported successfully",
                    path=bundle_path,
                    types=list(bundle["artifacts"].keys()),
                )
                click.echo("Bundle imported successfully")

        except Exception as e:
            logger.error(
                "Failed to import bundle",
                error=str(e),
                path=bundle_path,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("query")
    @click.option("--type", "-t", help="Filter by artifact type")
    @click.option("--tag", multiple=True, help="Filter by tags")
    def search(query: str, type: Optional[str], tag: tuple[str, ...]) -> None:
        """Search for artifacts using semantic search.

        This command uses vector embeddings to find semantically similar artifacts.
        Results are ranked by relevance to the query.
        """
        try:
            # Initialize vector store
            store = VectorStore()

            # Search artifacts
            results = store.search(
                query=query,
                artifact_type=type,
                tags=list(tag) if tag else None,
                limit=10,
            )

            # Display results
            click.echo("\nSearch Results:")
            click.echo("=" * 80)
            for result in results:
                click.echo(f"\nScore: {result.score:.2f}")
                click.echo(f"Type: {result.artifact_type}")
                click.echo(f"Name: {result.name}")
                click.echo(f"Version: {result.version}")
                if result.description:
                    click.echo(f"Description: {result.description}")
                if result.tags:
                    click.echo(f"Tags: {', '.join(result.tags)}")
                click.echo("-" * 40)

        except Exception as e:
            logger.error(
                "Search failed",
                error=str(e),
                query=query,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.option("--type", "-t", help="Filter by artifact type")
    @click.option(
        "--period", "-p", default="24h", help="Time period (e.g., 24h, 7d, 30d)"
    )
    def stats(type: Optional[str], period: str) -> None:
        """Show usage statistics and metrics for artifacts.

        This command displays various metrics like:
        - Usage frequency
        - Success/failure rates
        - Average response times
        - Resource utilization
        """
        try:
            # Get metrics from monitoring system
            stats = metrics.get_stats(artifact_type=type, period=period)

            # Display statistics
            click.echo("\nUsage Statistics:")
            click.echo("=" * 80)

            if "usage" in stats:
                click.echo("\nUsage Metrics:")
                for metric, value in stats["usage"].items():
                    click.echo(f"  {metric}: {value}")

            if "performance" in stats:
                click.echo("\nPerformance Metrics:")
                for metric, value in stats["performance"].items():
                    click.echo(f"  {metric}: {value}")

            if "errors" in stats:
                click.echo("\nError Rates:")
                for error_type, count in stats["errors"].items():
                    click.echo(f"  {error_type}: {count}")

        except Exception as e:
            logger.error(
                "Failed to get statistics",
                error=str(e),
                type=type,
                period=period,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.group()
    def chain():
        """Manage processing chains and pipelines."""
        pass

    @staticmethod
    @chain.command()
    @click.argument("chain_name")
    @click.option("--version", "-v", default=None, help="Chain version to run")
    def run_chain(chain_name: str, version: Optional[str]) -> None:
        """Run a processing chain from the hub."""
        try:
            # Initialize hub
            hub = Hub(storage_dir=HUB_DIR)

            # Load chain configuration
            chain_config = hub.load_artifact("chains", chain_name, version)

            # Execute chain
            click.echo(f"Running chain '{chain_name}'...")
            # TODO: Implement chain execution logic

        except Exception as e:
            logger.error(
                "Failed to run chain",
                error=str(e),
                chain=chain_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.group()
    def memory():
        """Manage agent memory and knowledge bases."""
        pass

    @staticmethod
    @memory.command()
    @click.argument("agent_name")
    def clear_memory(agent_name: str) -> None:
        """Clear an agent's memory."""
        try:
            memory_manager = MemoryManager()
            memory_manager.clear_agent_memory(agent_name)
            click.echo(f"Memory cleared for agent '{agent_name}'")

        except Exception as e:
            logger.error(
                "Failed to clear memory",
                error=str(e),
                agent=agent_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.group()
    def plugin():
        """Manage hub plugins."""
        pass

    @staticmethod
    @plugin.command()
    @click.argument("plugin_name")
    def install_plugin(plugin_name: str) -> None:
        """Install a plugin from the hub."""
        try:
            hub = Hub(storage_dir=HUB_DIR)
            hub.install_plugin(plugin_name)
            click.echo(f"Plugin '{plugin_name}' installed successfully")

        except Exception as e:
            logger.error(
                "Failed to install plugin",
                error=str(e),
                plugin=plugin_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument(
        "artifact_type", type=click.Choice(["prompt", "agent", "workflow", "chain"])
    )
    @click.argument("artifact_name")
    @click.option("--version", "-v", default=None, help="Version to test")
    def test(artifact_type: str, artifact_name: str, version: Optional[str]) -> None:
        """Run tests for an artifact.

        This command executes the test suite for the specified artifact,
        validating its behavior and performance.
        """
        try:
            hub = Hub(storage_dir=HUB_DIR)

            # Load and run tests
            results = hub.run_tests(artifact_type, artifact_name, version)

            # Display results
            click.echo("\nTest Results:")
            click.echo("=" * 80)

            for test in results:
                status = "✓" if test.passed else "✗"
                click.echo(f"\n{status} {test.name}")
                if not test.passed:
                    click.echo(f"  Error: {test.error}")
                if test.performance:
                    click.echo(f"  Performance: {test.performance}")

        except Exception as e:
            logger.error(
                "Failed to run tests",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument(
        "artifact_type", type=click.Choice(["prompt", "agent", "workflow", "chain"])
    )
    @click.argument("artifact_name")
    @click.option("--version", "-v", default=None, help="Version to document")
    @click.option(
        "--format", "-f", default="markdown", type=click.Choice(["markdown", "html"])
    )
    def docs(
        artifact_type: str,
        artifact_name: str,
        version: Optional[str],
        format: str,
    ) -> None:
        """Generate documentation for an artifact.

        This command creates comprehensive documentation including:
        - Usage examples
        - Configuration options
        - Dependencies
        - Performance characteristics
        """
        try:
            hub = Hub(storage_dir=HUB_DIR)

            # Generate documentation
            docs = hub.generate_docs(
                artifact_type,
                artifact_name,
                version=version,
                format=format,
            )

            # Display or save documentation
            if format == "markdown":
                click.echo(docs)
            else:
                output_file = f"{artifact_name}_docs.html"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(docs)
                click.echo(f"Documentation saved to {output_file}")

        except Exception as e:
            logger.error(
                "Failed to generate documentation",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                version=version,
            )
            click.echo(f"Error: {str(e)}")


# Register the hub commands
from pepperpy.cli import CLIManager

CLIManager.register_group(HubCommands)
