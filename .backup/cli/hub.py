"""CLI commands for managing local artifacts in the Pepper Hub.

This module provides commands for managing artifacts (prompts, agents, workflows)
in the local Pepper Hub, including pushing, pulling, listing, and executing.
"""

from pathlib import Path
from typing import Optional

import click
import yaml

from pepperpy.cli import CommandGroup, logger
from pepperpy.core.errors import ValidationError
from pepperpy.hub import Hub
from pepperpy.memory import MemoryManager

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
        hub.add_command(cls.get_chain_group())
        hub.add_command(cls.get_memory_group())
        hub.add_command(cls.get_plugin_group())

        return hub

    @classmethod
    def get_chain_group(cls) -> click.Group:
        """Get the chain command group."""

        @click.group(name="chain")
        def chain():
            """Manage processing chains and pipelines."""
            pass

        @chain.command()
        @click.argument("chain_name")
        @click.option("--version", "-v", default=None, help="Chain version to run")
        def run(chain_name: str, version: Optional[str]) -> None:
            """Run a processing chain from the hub."""
            try:
                # Initialize hub
                hub = Hub(storage_dir=HUB_DIR)

                # Load chain configuration
                chain = hub.load_artifact("chains", chain_name, version)

                # Execute chain
                click.echo(f"Running chain '{chain_name}'...")
                click.echo(chain)

            except Exception as e:
                logger.error(
                    "Failed to run chain",
                    error=str(e),
                    chain=chain_name,
                    version=version,
                )
                click.echo(f"Error: {str(e)}")
                raise click.Abort()

        return chain

    @classmethod
    def get_memory_group(cls) -> click.Group:
        """Get the memory command group."""

        @click.group(name="memory")
        def memory():
            """Manage agent memory and knowledge bases."""
            pass

        @memory.command()
        @click.argument("agent_name")
        async def clear_memory(agent_name: str) -> None:
            """Clear memory for an agent."""
            try:
                from pepperpy.memory.stores.inmemory import InMemoryStore

                memory_manager = MemoryManager()
                store = InMemoryStore({})
                await memory_manager.register_store("agent", store)
                await memory_manager.cleanup()
                click.echo(f"Memory cleared for agent {agent_name}")
            except Exception as e:
                logger.error(
                    "Failed to clear memory",
                    error=str(e),
                    agent_name=agent_name,
                )
                click.echo(f"Error: {str(e)}")

        return memory

    @classmethod
    def get_plugin_group(cls) -> click.Group:
        """Get the plugin command group."""

        @click.group(name="plugin")
        def plugin():
            """Manage hub plugins."""
            pass

        @plugin.command()
        @click.argument("plugin_name")
        def install(plugin_name: str) -> None:
            """Install a plugin from the hub."""
            try:
                hub = Hub(storage_dir=HUB_DIR)
                hub.save_artifact("plugins", plugin_name, {})
                click.echo(f"Plugin '{plugin_name}' installed successfully")

        except Exception as e:
            logger.error(
                    "Failed to install plugin",
                error=str(e),
                    plugin=plugin_name,
            )
            click.echo(f"Error: {str(e)}")
                raise click.Abort()

        return plugin

    @staticmethod
    @click.command()
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    @click.argument("artifact_name")
    @click.option("--version", "-v", default=None, help="Optional version to remove.")
    def remove(artifact_type: str, artifact_name: str, version: Optional[str]) -> None:
        """Remove an artifact or a specific version of it from the local hub."""
        try:
            hub = Hub(storage_dir=HUB_DIR)
            hub.delete_artifact(artifact_type, artifact_name, version)
            click.echo(f"Removed artifact '{artifact_name}'")

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
        "--version", "-v", default=None, help="Specify artifact version to show."
    )
    def show(artifact_type: str, artifact_name: str, version: Optional[str]) -> None:
        """Display the YAML content of an artifact in the local hub.

        If no version is specified, shows the latest version.
        """
        try:
            hub = Hub(storage_dir=HUB_DIR)
            artifact = hub.load_artifact(artifact_type, artifact_name, version)
            click.echo(yaml.dump(artifact))

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
            hub = Hub(storage_dir=HUB_DIR)
            artifacts = hub.list_artifacts(artifact_type)

            for artifact in artifacts:
                if artifact["name"] == artifact_name:
            if version:
                        if version in artifact["versions"]:
                            click.echo(
                                f"Artifact '{artifact_name}' has version '{version}'"
                            )
            else:
                click.echo(f"Versions for '{artifact_name}':")
                        for v in artifact["versions"]:
                    click.echo(f"  - {v}")
                        return

            raise ValidationError(f"Artifact '{artifact_name}' not found.")

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
            hub = Hub(storage_dir=HUB_DIR)
            artifact = hub.load_artifact(artifact_type, artifact_name, version)

            with open(output_path, "w") as f:
                yaml.dump(artifact, f)

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
    @click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
    def list(artifact_type: Optional[str]) -> None:
        """List artifacts in the local hub."""
        try:
            hub = Hub(storage_dir=HUB_DIR)
            artifacts = hub.list_artifacts(artifact_type)

            if not artifacts:
                click.echo("No artifacts found.")
                return

            for artifact in artifacts:
                click.echo(f"\n{artifact['name']}:")
                click.echo(f"  Type: {artifact['type']}")
                click.echo(f"  Latest Version: {artifact['latest_version']}")
                click.echo(f"  Versions: {', '.join(artifact['versions'])}")

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
    @click.argument("file_path", type=click.Path(exists=True))
    @click.option("--version", "-v", default=None, help="Version to push.")
    def push(
        artifact_type: str, artifact_name: str, file_path: str, version: Optional[str]
    ) -> None:
        """Push (import) an artifact from a file to the local hub."""
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            hub = Hub(storage_dir=HUB_DIR)
            hub.save_artifact(artifact_type, artifact_name, data, version)
            click.echo(f"Artifact '{artifact_name}' pushed successfully.")

        except Exception as e:
            logger.error(
                "Failed to push artifact",
                error=str(e),
                type=artifact_type,
                name=artifact_name,
                file=file_path,
                version=version,
            )
            click.echo(f"Error: {str(e)}")


# Register the hub commands
from pepperpy.cli import CLIManager

CLIManager.register_group(HubCommands)
