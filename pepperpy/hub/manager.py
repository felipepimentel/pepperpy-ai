"""Hub manager module.

This module provides the HubManager class for managing Hub instances
and their lifecycle.
"""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set
from uuid import UUID

import yaml

from pepperpy.core.errors import HubError, NotFoundError, PepperpyError
from pepperpy.core.types import ComponentState
from pepperpy.core.workflows import WorkflowEngine
from pepperpy.events.base import EventBus
from pepperpy.hub.base import Hub, HubConfig, HubType
from pepperpy.hub.errors import HubNotFoundError
from pepperpy.hub.events import HubArtifactEvent, HubEventHandler, HubLifecycleEvent
from pepperpy.hub.marketplace import MarketplaceManager
from pepperpy.hub.security import SecurityManager
from pepperpy.hub.storage.base import StorageBackend, StorageMetadata
from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)


class HubManager:
    """Manages Hub instances and their lifecycle."""

    _instance: Optional["HubManager"] = None
    _hub_path: Path = Path(os.getenv("PEPPER_HUB_PATH", ".pepper_hub"))

    def __init__(self, hub_path: Optional[str] = None) -> None:
        """Initialize hub manager.

        Args:
            hub_path: Optional path to Hub directory
        """
        if hub_path:
            self._hub_path = Path(hub_path)
        self._root_dir = self._hub_path
        self._storage_backend = None
        self._security_manager = None
        self._marketplace_manager = None
        self._event_bus = EventBus()
        self._event_handler = HubEventHandler()
        self._hubs: Dict[str, Hub] = {}
        self._active = False
        self._watchers: Dict[str, Set[asyncio.Task]] = {}
        self._workflow_engine = WorkflowEngine()
        self._component_states: Dict[str, ComponentState] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "HubManager":
        """Get singleton instance.

        Returns:
            HubManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def storage_backend(self) -> Optional[StorageBackend]:
        """Get storage backend."""
        return self._storage_backend

    @storage_backend.setter
    def storage_backend(self, backend: StorageBackend) -> None:
        """Set storage backend."""
        self._storage_backend = backend

    @property
    def security_manager(self) -> Optional[SecurityManager]:
        """Get security manager."""
        return self._security_manager

    @security_manager.setter
    def security_manager(self, manager: SecurityManager) -> None:
        """Set security manager."""
        self._security_manager = manager

    @property
    def marketplace_manager(self) -> Optional[MarketplaceManager]:
        """Get marketplace manager."""
        return self._marketplace_manager

    @marketplace_manager.setter
    def marketplace_manager(self, manager: MarketplaceManager) -> None:
        """Set marketplace manager."""
        self._marketplace_manager = manager

    @property
    def root_dir(self) -> Path:
        """Get the root directory.

        Returns:
            Root directory path
        """
        return self._root_dir

    async def initialize(self) -> None:
        """Initialize Hub manager."""
        try:
            # Initialize components
            if self._storage_backend:
                await self._storage_backend.initialize()
            if self._security_manager:
                await self._security_manager.initialize()
            if self._marketplace_manager:
                await self._marketplace_manager.initialize()

            # Initialize workflow engine
            await self._workflow_engine.initialize()

            # Register event handler
            self._event_bus.add_handler(self._event_handler)

            # Load existing hubs
            await self._load_hubs()

            self._active = True
            logger.info("Hub manager initialized", extra={"status": "success"})

        except Exception as e:
            logger.error("Failed to initialize Hub manager", extra={"error": str(e)})
            raise

    async def cleanup(self) -> None:
        """Clean up Hub manager."""
        try:
            # Clean up components
            if self._storage_backend:
                await self._storage_backend.close()
            if self._security_manager:
                await self._security_manager.cleanup()
            if self._marketplace_manager:
                await self._marketplace_manager.cleanup()

            # Clean up workflow engine
            await self._workflow_engine.cleanup()

            # Clean up hubs
            for hub_name in list(self._hubs.keys()):
                await self._cleanup_hub(hub_name)

            self._active = False
            logger.info("Hub manager cleaned up", extra={"status": "success"})

        except Exception as e:
            logger.error("Failed to clean up Hub manager", extra={"error": str(e)})
            raise

    async def _cleanup_hub(self, hub_name: str) -> None:
        """Clean up a hub's resources.

        Args:
            hub_name: Name of hub to clean up
        """
        try:
            if hub := self._hubs.get(hub_name):
                await hub.cleanup()
                del self._hubs[hub_name]
                logger.info(f"Cleaned up hub: {hub_name}")

        except Exception as e:
            logger.error(f"Failed to clean up hub {hub_name}: {e}")

    async def _load_hubs(self) -> None:
        """Load existing hubs from manifest files."""
        try:
            manifest_dir = self.root_dir / "manifests"
            for manifest_path in manifest_dir.glob("*.json"):
                try:
                    # Validate manifest signature if security manager is present
                    if self._security_manager:
                        await self._security_manager.validate_signature(manifest_path)

                    # Load and validate manifest
                    config = await self._load_and_validate_manifest(manifest_path)

                    # Register hub
                    await self.register_hub(config.name, config)

                    # Set up file watching if enabled
                    if config.enable_hot_reload:
                        await self._setup_hub_watcher(config.name, manifest_path)

                except Exception as e:
                    logger.error(
                        f"Failed to load hub from {manifest_path}: {e}", exc_info=True
                    )

        except Exception as e:
            raise HubError(f"Failed to load hubs: {e}")

    async def _load_and_validate_manifest(self, manifest_path: Path) -> HubConfig:
        """Load and validate a hub manifest.

        Args:
            manifest_path: Path to manifest file

        Returns:
            HubConfig: Validated hub configuration

        Raises:
            HubError: If manifest is invalid
        """
        try:
            with open(manifest_path) as f:
                data = json.load(f)

            # Add required fields
            if "name" not in data:
                data["name"] = manifest_path.stem
            if "type" not in data:
                data["type"] = HubType.LOCAL
            if "resources" not in data:
                data["resources"] = []
            if "workflows" not in data:
                data["workflows"] = []

            config = HubConfig(**data)
            config.manifest_path = manifest_path
            return config

        except Exception as e:
            raise HubError(f"Invalid hub manifest: {e}")

    async def _setup_hub_watcher(self, hub_name: str, path: Path) -> None:
        """Set up file watcher for a Hub.

        Args:
            hub_name: Hub name
            path: Path to watch
        """
        try:
            # Create directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)

            # Set up watcher
            await self.watch(hub_name, str(path), self._on_file_change)

        except Exception as e:
            logger.error(
                f"Failed to set up Hub watcher: {hub_name}", extra={"error": str(e)}
            )
            raise HubError(f"Failed to set up Hub watcher: {str(e)}")

    async def _on_file_change(self, path: str) -> None:
        """Handle file change event.

        Args:
            path: Changed file path
        """
        try:
            # Get hub name from path
            hub_name = Path(path).parent.name
            if hub_name not in self._hubs:
                return

            # Reload hub
            await self._reload_hub(hub_name)
            logger.info(f"Reloaded hub: {hub_name}")

        except Exception as e:
            logger.error(
                f"Failed to handle file change: {path}", extra={"error": str(e)}
            )

    async def _watch_hub_changes(self, hub_name: str, hub_path: Path) -> None:
        """Watch for changes in hub files.

        Args:
            hub_name: Name of hub to watch
            hub_path: Path to watch
        """
        try:
            while True:
                if await self._detect_hub_changes(hub_name, hub_path):
                    await self._reload_hub(hub_name)
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Hub watcher failed for {hub_name}: {e}")

    async def _detect_hub_changes(self, hub_name: str, hub_path: Path) -> bool:
        """Detect changes in hub files.

        Args:
            hub_name: Name of hub to check
            hub_path: Path to check

        Returns:
            bool: True if changes detected
        """
        # TODO[v2.0]: Implement proper file change detection
        return False

    async def _reload_hub(self, hub_name: str) -> None:
        """Reload a hub from its manifest.

        Args:
            hub_name: Name of hub to reload
        """
        try:
            # Get current hub
            hub = self._hubs.get(hub_name)
            if not hub:
                logger.warning(f"Hub not found for reload: {hub_name}")
                return

            # Clean up current hub
            await self._cleanup_hub(hub_name)

            # Reload hub from manifest
            if hub.config.manifest_path:
                config = await self._load_and_validate_manifest(
                    hub.config.manifest_path
                )
                await self.register_hub(hub_name, config)

                logger.info(f"Successfully reloaded hub: {hub_name}")

        except Exception as e:
            logger.error(f"Failed to reload hub {hub_name}: {e}")

    async def register_hub(
        self,
        name: str,
        config: HubConfig,
    ) -> Hub:
        """Register a new hub.

        Args:
            name: Hub name
            config: Hub configuration

        Returns:
            Hub: The registered hub instance

        Raises:
            HubError: If registration fails
        """
        try:
            # Create and initialize hub
            hub = Hub(name=name, config=config)
            await hub.initialize()
            self._hubs[name] = hub

            # Emit event
            event = HubLifecycleEvent(
                hub_name=name,
                operation="register",
                metadata={},
                config=config,
                state=ComponentState.INITIALIZED,
            )
            await self._event_bus.publish(event)

            logger.info(f"Hub registered: {name}")
            return hub

        except Exception:
            logger.error(f"Failed to register hub: {name}", exc_info=True)
            raise

    async def unregister_hub(self, name: str) -> None:
        """Unregister a hub.

        Args:
            name: Hub name to unregister

        Raises:
            HubError: If unregistration fails
        """
        try:
            # Clean up hub
            await self._cleanup_hub(name)

            # Emit event
            event = HubLifecycleEvent(
                hub_name=name,
                operation="unregister",
                metadata={},
                config=self._hubs[name].config,
                state=ComponentState.UNREGISTERED,
            )
            await self._event_bus.publish(event)

            # Remove from registry
            del self._hubs[name]

            logger.info(f"Hub unregistered: {name}")

        except Exception:
            logger.error(f"Failed to unregister hub: {name}", exc_info=True)
            raise

    async def get_hub(self, name: str) -> Hub:
        """Get a hub by name.

        Args:
            name: Hub name

        Returns:
            Hub: The hub instance

        Raises:
            HubError: If hub not found
        """
        if name not in self._hubs:
            raise ValueError(f"Hub not found: {name}")
        return self._hubs[name]

    async def watch(
        self, hub_name: str, path: str, callback: Callable[[str], Any]
    ) -> None:
        """Watch a path for changes.

        Args:
            hub_name: Hub name
            path: Path to watch
            callback: Callback function for changes

        Raises:
            HubNotFoundError: If Hub not found
            HubError: If watch setup fails
        """
        try:
            if hub_name not in self._hubs:
                raise HubNotFoundError(f"Hub not found: {hub_name}")

            # Create watcher task
            task = asyncio.create_task(self._watch_path(Path(path), callback))

            # Store task
            if hub_name not in self._watchers:
                self._watchers[hub_name] = set()
            self._watchers[hub_name].add(task)

        except HubNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to set up watcher: {path}", extra={"error": str(e)})
            raise HubError(f"Failed to set up watcher: {str(e)}")

    async def _watch_path(self, path: Path, callback: Callable[[str], Any]) -> None:
        """Watch a path for changes.

        Args:
            path: Path to watch
            callback: Callback to execute on changes
        """
        try:
            while True:
                if path.exists() and path.stat().st_mtime > time.time() - 1:
                    await callback(str(path))
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"File watcher failed for {path}: {e}")

    async def publish_artifact(
        self,
        hub_name: str,
        artifact_id: UUID,
        artifact_type: str,
        content: Dict[str, Any],
        version: str,
        visibility: str = "public",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish an artifact to a hub.

        Args:
            hub_name: Name of the hub
            artifact_id: Artifact ID
            artifact_type: Type of artifact
            content: Artifact content
            version: Artifact version
            visibility: Artifact visibility
            metadata: Additional metadata

        Raises:
            HubError: If hub not found or storage backend not configured
        """
        try:
            # Validate hub exists
            if hub_name not in self._hubs:
                raise HubError(f"Hub not found: {hub_name}")

            # Validate storage backend
            if not self.storage_backend:
                raise HubError("Storage backend not configured")

            # Convert content to string for size calculation
            content_str = json.dumps(content)
            content_size = len(content_str.encode())

            # Create storage metadata
            storage_metadata = StorageMetadata(
                id=str(artifact_id),
                name=f"{artifact_type}_{artifact_id}",
                version=version,
                artifact_type=artifact_type,
                size=content_size,
                hash=hashlib.sha256(content_str.encode()).hexdigest(),
            )

            # Store artifact
            await self.storage_backend.store(
                artifact_id=str(artifact_id),
                artifact_type=artifact_type,
                content=content,
                metadata=storage_metadata,
            )

            # Emit event
            event = HubArtifactEvent(
                hub_name=hub_name,
                operation="publish",
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                version=version,
                visibility=visibility,
                metadata=metadata,
            )
            await self._event_bus.publish(event)

        except Exception as e:
            logger.error(
                "Failed to publish artifact",
                extra={
                    "hub": hub_name,
                    "artifact_id": str(artifact_id),
                    "error": str(e),
                },
            )
            raise

    async def get_component_state(self, component_id: str) -> Optional[ComponentState]:
        """Get the state of a component.

        Args:
            component_id: ID of the component

        Returns:
            Component state if found, None otherwise
        """
        async with self._lock:
            return self._component_states.get(component_id)

    async def set_component_state(
        self, component_id: str, state: ComponentState
    ) -> None:
        """Set the state of a component.

        Args:
            component_id: ID of the component
            state: New component state
        """
        async with self._lock:
            self._component_states[component_id] = state

    async def remove_component_state(self, component_id: str) -> None:
        """Remove the state of a component.

        Args:
            component_id: ID of the component
        """
        async with self._lock:
            self._component_states.pop(component_id, None)

    async def initialize_component(self, component_id: str) -> None:
        """Initialize a component.

        Args:
            component_id: ID of the component
        """
        await self.set_component_state(component_id, ComponentState.INITIALIZED)

    async def unregister_component(self, component_id: str) -> None:
        """Unregister a component.

        Args:
            component_id: ID of the component
        """
        await self.set_component_state(component_id, ComponentState.UNREGISTERED)

    async def _initialize_hub(self, hub_name: str, config: HubConfig) -> None:
        """Initialize a hub.

        Args:
            hub_name: Name of the hub
            config: Hub configuration

        Raises:
            HubError: If initialization fails
        """
        try:
            # Initialize hub
            hub = Hub(hub_name, config)
            await hub.initialize()

            # Store hub
            self._hubs[hub_name] = hub

            # Set component state
            await self.set_component_state(hub_name, ComponentState.INITIALIZED)

            # Emit event
            event = HubLifecycleEvent(
                hub_name=hub_name,
                operation="initialize",
                config=config,
                state=ComponentState.INITIALIZED,
            )
            await self._event_bus.publish(event)

            # Setup file watching if enabled
            if config.enable_hot_reload:
                await self._setup_hub_watcher(hub_name, self.root_dir / hub_name)

            logger.info(f"Initialized hub: {hub_name}")

        except Exception as e:
            logger.error(f"Failed to initialize hub {hub_name}: {e}")
            await self.set_component_state(hub_name, ComponentState.ERROR)
            raise HubError(f"Failed to initialize hub {hub_name}") from e

    async def _unregister_hub(self, hub_name: str) -> None:
        """Unregister a hub.

        Args:
            hub_name: Name of the hub

        Raises:
            HubError: If unregistration fails
        """
        try:
            # Get hub
            hub = self._hubs.get(hub_name)
            if not hub:
                raise HubError(f"Hub not found: {hub_name}")

            # Get config for event
            config = hub.config

            # Cleanup hub
            await hub.cleanup()

            # Remove from registry
            del self._hubs[hub_name]

            # Set component state
            await self.set_component_state(hub_name, ComponentState.UNREGISTERED)

            # Emit event
            event = HubLifecycleEvent(
                hub_name=hub_name,
                operation="unregister",
                config=config,
                state=ComponentState.UNREGISTERED,
            )
            await self._event_bus.publish(event)

            logger.info(f"Unregistered hub: {hub_name}")

        except Exception as e:
            logger.error(f"Failed to unregister hub {hub_name}: {e}")
            await self.set_component_state(hub_name, ComponentState.ERROR)
            raise HubError(f"Failed to unregister hub {hub_name}") from e

    @classmethod
    def load(cls, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Load Hub artifact configuration.

        Args:
            name: Name of the artifact
            version: Optional version (defaults to latest)

        Returns:
            Artifact configuration

        Raises:
            PepperpyError: If loading fails
        """
        try:
            manager = cls.get_instance()

            # Find artifact directory
            artifact_dir = manager._find_artifact_dir(name)
            if not artifact_dir.exists():
                raise PepperpyError(f"Artifact not found: {name}")

            # Get version
            if version is None:
                version = manager._get_latest_version(artifact_dir)

            # Load configuration
            config_path = artifact_dir / f"v{version}.yaml"
            if not config_path.exists():
                raise PepperpyError(f"Version not found: {version}")

            with open(config_path) as f:
                return yaml.safe_load(f)

        except Exception as e:
            raise PepperpyError(f"Failed to load Hub artifact: {e}")

    def _find_artifact_dir(self, name: str) -> Path:
        """Find artifact directory.

        Args:
            name: Artifact name

        Returns:
            Path to artifact directory
        """
        # Check each subdirectory for artifact
        for subdir in self._hub_path.iterdir():
            if subdir.is_dir():
                artifact_dir = subdir / name
                if artifact_dir.exists():
                    return artifact_dir

        # Default to agents directory
        return self._hub_path / "agents" / name

    def _get_latest_version(self, artifact_dir: Path) -> str:
        """Get latest version from artifact directory.

        Args:
            artifact_dir: Path to artifact directory

        Returns:
            Latest version string

        Raises:
            PepperpyError: If no versions found
        """
        versions = []
        for path in artifact_dir.glob("v*.yaml"):
            version = path.stem[1:]  # Remove 'v' prefix
            versions.append(version)

        if not versions:
            raise PepperpyError("No versions found")

        return sorted(versions)[-1]  # Return highest version


class ResourceManager:
    """Manager for loading resource configurations."""

    @classmethod
    def load(cls, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Load resource configuration from Hub.

        Args:
            name: Resource name
            version: Optional version

        Returns:
            Resource configuration
        """
        return HubManager.load(f"resources/{name}", version=version)


class ErrorManager:
    """Manager for loading error definitions."""

    @classmethod
    def load(cls, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Load error definitions from Hub.

        Args:
            name: Error definition name
            version: Optional version

        Returns:
            Error definitions
        """
        return HubManager.load(f"errors/{name}", version=version)


class HubManager:
    """Manager for Hub-based resource configurations."""

    def __init__(self, hub_path: Optional[str] = None) -> None:
        """Initialize Hub manager.

        Args:
            hub_path: Optional path to Hub directory. Defaults to .pepper_hub
                     in the current directory.
        """
        self.hub_path = Path(hub_path or ".pepper_hub").resolve()
        if not self.hub_path.exists():
            raise HubError(f"Hub directory not found: {self.hub_path}")

    def load_config(
        self,
        resource_type: str,
        name: str,
        version: str = "v1.0.0",
    ) -> Dict[str, Any]:
        """Load resource configuration from Hub.

        Args:
            resource_type: Type of resource (e.g., 'memory', 'agent')
            name: Name of the resource
            version: Version of the configuration

        Returns:
            Resource configuration

        Raises:
            NotFoundError: If configuration not found
            HubError: If configuration loading fails
        """
        config_path = (
            self.hub_path / "resources" / resource_type / name / f"{version}.yaml"
        )

        if not config_path.exists():
            raise NotFoundError(
                f"Configuration not found: {config_path.relative_to(self.hub_path)}"
            )

        try:
            with config_path.open("r") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise HubError(f"Invalid configuration format: {config_path}")

            return config
        except Exception as e:
            raise HubError(f"Failed to load configuration: {e}")

    def save_config(
        self,
        resource_type: str,
        name: str,
        config: Dict[str, Any],
        version: str = "v1.0.0",
    ) -> None:
        """Save resource configuration to Hub.

        Args:
            resource_type: Type of resource
            name: Name of the resource
            config: Resource configuration
            version: Version of the configuration

        Raises:
            HubError: If configuration saving fails
        """
        config_dir = self.hub_path / "resources" / resource_type / name

        try:
            # Create directory if it doesn't exist
            config_dir.mkdir(parents=True, exist_ok=True)

            # Save configuration
            config_path = config_dir / f"{version}.yaml"
            with config_path.open("w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)
        except Exception as e:
            raise HubError(f"Failed to save configuration: {e}")

    def list_resources(
        self,
        resource_type: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """List available resources in the Hub.

        Args:
            resource_type: Optional resource type to filter by

        Returns:
            Dictionary of resource names to their latest configurations

        Raises:
            HubError: If listing resources fails
        """
        resources: Dict[str, Dict[str, Any]] = {}

        try:
            resources_dir = self.hub_path / "resources"
            if not resources_dir.exists():
                return resources

            # List all resource types or specific type
            types = [resource_type] if resource_type else os.listdir(resources_dir)

            for type_name in types:
                type_dir = resources_dir / type_name
                if not type_dir.is_dir():
                    continue

                # List resources of this type
                for resource_dir in type_dir.iterdir():
                    if not resource_dir.is_dir():
                        continue

                    # Find latest version
                    versions = sorted(
                        [f.stem for f in resource_dir.glob("*.yaml")],
                        reverse=True,
                    )
                    if not versions:
                        continue

                    # Load latest configuration
                    config = self.load_config(
                        type_name,
                        resource_dir.name,
                        versions[0],
                    )
                    resources[f"{type_name}/{resource_dir.name}"] = config

            return resources
        except Exception as e:
            raise HubError(f"Failed to list resources: {e}")


# Global Hub manager instance
_hub_manager: Optional[HubManager] = None


def get_hub_manager(hub_path: Optional[str] = None) -> HubManager:
    """Get or create global Hub manager instance.

    Args:
        hub_path: Optional path to Hub directory

    Returns:
        Hub manager instance
    """
    global _hub_manager
    if _hub_manager is None:
        _hub_manager = HubManager(hub_path)
    return _hub_manager
