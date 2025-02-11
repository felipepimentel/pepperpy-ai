"""CLI commands for managing local artifacts in the Pepper Hub.

This module provides commands for pushing, pulling, listing, and managing
artifacts in the local Pepper Hub.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

import click
import yaml

from pepperpy.core.errors import ValidationError
from pepperpy.monitoring import bind_logger

# Configure logger
logger = bind_logger(module="cli.hub")

# Default hub directory in user's home
HUB_DIR = Path.home() / ".pepper_hub"


def ensure_hub_structure() -> None:
    """Ensure the hub directory structure exists."""
    HUB_DIR.mkdir(exist_ok=True)
    for artifact_type in ["prompts", "agents", "workflows"]:
        (HUB_DIR / artifact_type).mkdir(exist_ok=True)


@click.group()
def hub() -> None:
    """Manage local Pepper Hub artifacts (prompts, agents, workflows)."""
    ensure_hub_structure()


@hub.command()
@click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), required=True, help="Path to the artifact file")
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
                import json
                data = json.load(f)
            else:
                raise ValidationError("Unsupported file extension. Please use YAML or JSON.")

        # Validate minimal fields
        name = data.get("name")
        version = data.get("version")
        if not name or not version:
            raise ValidationError("Artifact file must contain 'name' and 'version'.")

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
        click.echo(f"Artifact '{name}' version '{version}' pushed to local hub ({artifact_type}s).")

    except Exception as e:
        logger.error(
            "Failed to push artifact",
            error=str(e),
            file=file_path,
            type=artifact_type,
        )
        click.echo(f"Error: {str(e)}")


@hub.command()
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
            artifact_names = sorted([d for d in os.listdir(type_path) if (type_path / d).is_dir()])
            click.echo(f"{t}:")
            for art_name in artifact_names:
                art_dir = type_path / art_name
                versions = sorted([v.replace(".yaml", "") for v in os.listdir(art_dir) if v.endswith(".yaml")])
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


@hub.command()
@click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
@click.argument("artifact_name")
@click.option("--version", "-v", default=None, help="Specify artifact version to show.")
def show(artifact_type: str, artifact_name: str, version: Optional[str]) -> None:
    """Display the YAML content of an artifact in the local hub.

    If no version is specified, shows the latest version.
    """
    try:
        art_dir = HUB_DIR / f"{artifact_type}s" / artifact_name
        if not art_dir.exists():
            raise ValidationError("Artifact not found.")

        all_versions = sorted([f for f in os.listdir(art_dir) if f.endswith(".yaml")])
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


@hub.command()
@click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
@click.argument("artifact_name")
@click.option("--version", "-v", default=None, help="List a specific version or all versions.")
def versions(artifact_type: str, artifact_name: str, version: Optional[str]) -> None:
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


@hub.command()
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


@hub.command()
@click.argument("artifact_type", type=click.Choice(["prompt", "agent", "workflow"]))
@click.argument("artifact_name")
@click.option("--version", "-v", default=None, help="Specify artifact version to pull.")
@click.option("-o", "--output", "output_path", type=click.Path(), required=True, help="Output file path")
def pull(artifact_type: str, artifact_name: str, version: Optional[str], output_path: str) -> None:
    """Pull (export) an artifact from the local hub to a file."""
    try:
        art_dir = HUB_DIR / f"{artifact_type}s" / artifact_name
        if not art_dir.exists():
            raise ValidationError("Artifact not found.")

        all_versions = sorted([f for f in os.listdir(art_dir) if f.endswith(".yaml")])
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