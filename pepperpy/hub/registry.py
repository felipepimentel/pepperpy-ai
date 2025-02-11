"""Registry system for managing Pepperpy artifacts.

This module provides centralized registry functionality for managing agents,
workflows, and other artifacts in the .pepper_hub directory.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from packaging import version
from pydantic import BaseModel, ValidationError

from pepperpy.core.errors import ConfigurationError
from pepperpy.monitoring import logger

log = logger.bind(module="registry")


class ArtifactMetadata(BaseModel):
    """Base metadata for any artifact."""

    name: str
    type: str
    version: str
    description: str
    tags: List[str]
    content: Dict[str, Any]
    metadata: Dict[str, Any]


class AgentMetadata(ArtifactMetadata):
    """Metadata for an agent version."""

    type: str = "agent"


class WorkflowMetadata(ArtifactMetadata):
    """Metadata for a workflow version."""

    type: str = "workflow"


class BaseRegistry:
    """Base class for artifact registries."""

    def __init__(self, hub_path: Optional[Path] = None):
        """Initialize the registry.

        Args:
        ----
            hub_path: Optional path to the hub directory. If not provided,
                     will use PEPPERPY_HUB_PATH env var or default to ~/.pepper_hub

        """
        self.hub_path = hub_path or Path(
            os.getenv("PEPPERPY_HUB_PATH", str(Path.home() / ".pepper_hub"))
        )
        self._cache: Dict[str, Dict[str, ArtifactMetadata]] = {}

    def _get_latest_version(self, artifact_type: str) -> str:
        """Get the latest version using semantic versioning.

        Args:
        ----
            artifact_type: Type of artifact to get latest version for

        Returns:
        -------
            Latest version string

        Raises:
        ------
            ValueError: If no versions found

        """
        if not self._cache.get(artifact_type):
            raise ValueError(f"No versions found for: {artifact_type}")

        versions = sorted(
            self._cache[artifact_type].keys(),
            key=lambda v: version.parse(v),
            reverse=True,
        )
        return versions[0]

    def _load_artifact(
        self, path: Path, metadata_class: type[ArtifactMetadata]
    ) -> ArtifactMetadata:
        """Load an artifact from a file.

        Args:
        ----
            path: Path to the artifact file
            metadata_class: Class to use for parsing metadata

        Returns:
        -------
            Parsed artifact metadata

        Raises:
        ------
            ConfigurationError: If loading fails

        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return metadata_class(**data)
        except Exception as e:
            raise ConfigurationError(f"Failed to load {path}: {e}")


class AgentRegistry(BaseRegistry):
    """Registry for managing agent configurations."""

    async def get_agent_config(
        self, agent_type: str, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get the configuration for an agent.

        Args:
        ----
            agent_type: Type of agent to get config for
            version: Optional specific version to get. If not provided,
                    will return the latest version.

        Returns:
        -------
            Agent configuration dictionary

        Raises:
        ------
            ValueError: If agent_type is invalid or version not found
            ConfigurationError: If configuration is invalid

        """
        # Load configurations if not cached
        if agent_type not in self._cache:
            await self._load_agent_configs(agent_type)

        if not self._cache.get(agent_type):
            raise ValueError(f"Invalid agent type: {agent_type}")

        # Get specific version or latest
        if version:
            if version not in self._cache[agent_type]:
                raise ValueError(f"Version {version} not found for agent {agent_type}")
            agent_meta = self._cache[agent_type][version]
        else:
            # Get latest version using semantic versioning
            latest = self._get_latest_version(agent_type)
            agent_meta = self._cache[agent_type][latest]

        return agent_meta.content

    async def _load_agent_configs(self, agent_type: str) -> None:
        """Load all configurations for an agent type."""
        agent_dir = self.hub_path / "agents" / agent_type
        if not agent_dir.exists():
            log.warning(f"Agent directory not found: {agent_dir}")
            return

        try:
            self._cache[agent_type] = {}
            for config_file in agent_dir.glob("*.yaml"):
                try:
                    metadata = self._load_artifact(config_file, AgentMetadata)
                    self._cache[agent_type][metadata.version] = metadata
                except Exception as e:
                    log.error(
                        "Failed to load agent config",
                        file=str(config_file),
                        error=str(e),
                    )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configurations for {agent_type}: {str(e)}"
            )


class WorkflowRegistry(BaseRegistry):
    """Registry for managing workflow configurations."""

    def __init__(self, hub_path: Optional[Path] = None):
        """Initialize the workflow registry."""
        super().__init__(hub_path)
        self.templates_path = self.hub_path / "templates" / "workflows"

    def list_workflows(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available workflows.

        Args:
        ----
            tag: Optional tag to filter by

        Returns:
        -------
            List of workflow metadata

        """
        workflows = []
        workflows_dir = self.hub_path / "workflows"

        for workflow_dir in workflows_dir.glob("**/[!.]*"):
            if not workflow_dir.is_dir():
                continue

            try:
                # Get the latest version
                versions = sorted(
                    workflow_dir.glob("*.yaml"),
                    key=lambda p: version.parse(p.stem),
                    reverse=True,
                )
                if not versions:
                    continue

                metadata = self._load_artifact(versions[0], WorkflowMetadata)

                if tag and tag not in metadata.tags:
                    continue

                workflows.append(metadata.dict())

            except Exception as e:
                log.warning(f"Failed to load workflow from {workflow_dir}: {e}")

        return workflows

    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get detailed information about a workflow.

        Args:
        ----
            workflow_name: Name of the workflow

        Returns:
        -------
            Workflow metadata and configuration

        Raises:
        ------
            ValueError: If workflow not found

        """
        workflow_path = self._get_workflow_path(workflow_name)
        if not workflow_path.exists():
            raise ValueError(f"Workflow not found: {workflow_name}")

        metadata = self._load_artifact(workflow_path, WorkflowMetadata)
        return metadata.dict()

    def validate_workflow(self, path: Path) -> List[str]:
        """Validate a workflow configuration file.

        Args:
        ----
            path: Path to the workflow file

        Returns:
        -------
            List of validation issues (empty if valid)

        """
        issues = []
        try:
            metadata = self._load_artifact(path, WorkflowMetadata)

            # Validate required sections
            if not metadata.content.get("steps"):
                issues.append("No steps defined")

            # Validate step structure
            for i, step in enumerate(metadata.content.get("steps", [])):
                if not step.get("name"):
                    issues.append(f"Step {i+1} missing name")
                if not step.get("agent"):
                    issues.append(f"Step {i+1} missing agent")
                if not step.get("action"):
                    issues.append(f"Step {i+1} missing action")

            # Validate schemas
            if not metadata.content.get("input_schema"):
                issues.append("Missing input schema")
            if not metadata.content.get("output_schema"):
                issues.append("Missing output schema")

        except ValidationError as e:
            for error in e.errors():
                issues.append(f"{error['loc']}: {error['msg']}")
        except Exception as e:
            issues.append(str(e))

        return issues

    def create_workflow(self, name: str, template: str = "basic") -> Path:
        """Create a new workflow from a template.

        Args:
        ----
            name: Name for the new workflow
            template: Template to use (default: "basic")

        Returns:
        -------
            Path to the created workflow file

        Raises:
        ------
            ValueError: If template not found
            ConfigurationError: If creation fails

        """
        template_path = self.templates_path / f"{template}.yaml"
        if not template_path.exists():
            raise ValueError(f"Template not found: {template}")

        # Create workflow directory
        workflow_dir = self.hub_path / "workflows" / name
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # Copy and customize template
        workflow_path = workflow_dir / "1.0.0.yaml"
        shutil.copy(template_path, workflow_path)

        try:
            # Update workflow metadata
            with open(workflow_path) as f:
                data = yaml.safe_load(f)

            data["name"] = name
            data["version"] = "1.0.0"

            with open(workflow_path, "w") as f:
                yaml.safe_dump(data, f)

            return workflow_path

        except Exception as e:
            raise ConfigurationError(f"Failed to create workflow: {e}")

    def _get_workflow_path(self, workflow_name: str) -> Path:
        """Get the path to a workflow's latest version."""
        parts = workflow_name.split("/")
        workflow_dir = self.hub_path / "workflows" / "/".join(parts)

        if not workflow_dir.exists():
            raise ValueError(f"Workflow not found: {workflow_name}")

        versions = sorted(
            workflow_dir.glob("*.yaml"),
            key=lambda p: version.parse(p.stem),
            reverse=True,
        )

        if not versions:
            raise ValueError(f"No versions found for workflow: {workflow_name}")

        return versions[0]

    async def get_workflow(
        self, workflow_name: str, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a workflow configuration.

        Args:
        ----
            workflow_name: Name of the workflow
            version: Optional specific version to get. If not provided,
                    will return the latest version.

        Returns:
        -------
            Workflow configuration

        Raises:
        ------
            ValueError: If workflow not found
            ConfigurationError: If configuration is invalid

        """
        workflow_path = self._get_workflow_path(workflow_name)
        if not workflow_path.exists():
            raise ValueError(f"Workflow not found: {workflow_name}")

        metadata = self._load_artifact(workflow_path, WorkflowMetadata)
        return metadata.dict()

    async def get_agent(
        self, agent_name: str, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get an agent configuration.

        Args:
        ----
            agent_name: Name of the agent
            version: Optional specific version to get. If not provided,
                    will return the latest version.

        Returns:
        -------
            Agent configuration

        Raises:
        ------
            ValueError: If agent not found
            ConfigurationError: If configuration is invalid

        """
        agent_path = self._get_agent_path(agent_name)
        if not agent_path.exists():
            raise ValueError(f"Agent not found: {agent_name}")

        metadata = self._load_artifact(agent_path, AgentMetadata)
        return metadata.dict()

    def _get_agent_path(self, agent_name: str) -> Path:
        """Get the path to an agent's latest version."""
        parts = agent_name.split("/")
        agent_dir = self.hub_path / "agents" / "/".join(parts)

        if not agent_dir.exists():
            raise ValueError(f"Agent not found: {agent_name}")

        versions = sorted(
            agent_dir.glob("*.yaml"),
            key=lambda p: version.parse(p.stem),
            reverse=True,
        )

        if not versions:
            raise ValueError(f"No versions found for agent: {agent_name}")

        return versions[0]
