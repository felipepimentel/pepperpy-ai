"""Hub management system."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Set

from pepperpy.core.lifecycle import ComponentState, Lifecycle

from .base import Hub, HubConfig
from .errors import (
    HubError,
    HubNotFoundError,
    HubValidationError,
)

logger = logging.getLogger(__name__)


class HubManager(Lifecycle):
    """Central manager for hub lifecycle and operations.

    Features:
    - Hub registration and validation
    - Resource management and discovery
    - Workflow coordination
    - State tracking and monitoring
    - Hot-reload support for development
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        """Initialize hub manager.

        Args:
            root_dir: Optional root directory for local resources

        """
        super().__init__()
        self.root_dir = root_dir
        self._hubs: Dict[str, Hub] = {}
        self._watchers: Dict[str, Set[asyncio.Task]] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the hub manager.

        This method:
        1. Validates the root directory
        2. Loads any existing hubs

        Raises:
            HubValidationError: If initialization fails

        """
        self._state = ComponentState.INITIALIZING
        try:
            if self.root_dir:
                if not self.root_dir.exists():
                    raise HubValidationError(
                        f"Root directory {self.root_dir} does not exist",
                        hub="manager",
                    )
                await self._load_hubs()

            self._state = ComponentState.INITIALIZED
        except Exception as e:
            self._state = ComponentState.ERROR
            self._error = e
            raise

    async def cleanup(self) -> None:
        """Clean up hub manager resources.

        This method:
        1. Stops all file watchers
        2. Shuts down all hubs

        Raises:
            HubError: If cleanup fails

        """
        try:
            # Stop file watchers
            for tasks in self._watchers.values():
                for task in tasks:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Shut down hubs in reverse registration order
            for hub_name in reversed(list(self._hubs)):
                await self._cleanup_hub(hub_name)

            self._state = ComponentState.TERMINATED
        except Exception as e:
            self._state = ComponentState.ERROR
            self._error = e
            raise

    async def register(
        self,
        name: str,
        config: HubConfig,
    ) -> Hub:
        """Register a new hub.

        Args:
            name: Hub name
            config: Hub configuration

        Returns:
            Registered hub instance

        Raises:
            HubValidationError: If registration fails

        """
        async with self._lock:
            if name in self._hubs:
                raise HubValidationError(
                    f"Hub {name} already registered",
                    hub=name,
                )

            try:
                hub = Hub(name, config)
                await hub.initialize()
                self._hubs[name] = hub
                logger.info(
                    f"Registered hub {name}",
                    extra={
                        "hub": name,
                        "type": config.type.value,
                    },
                )
                return hub
            except Exception as e:
                raise HubValidationError(
                    f"Failed to register hub: {e}",
                    hub=name,
                )

    async def get(self, name: str) -> Hub:
        """Get a registered hub.

        Args:
            name: Hub name

        Returns:
            Hub instance

        Raises:
            HubNotFoundError: If hub is not found

        """
        hub = self._hubs.get(name)
        if not hub:
            raise HubNotFoundError(name)
        return hub

    async def unregister(self, name: str) -> None:
        """Unregister a hub.

        Args:
            name: Hub name

        Raises:
            HubNotFoundError: If hub is not found
            HubError: If unregistration fails

        """
        hub = await self.get(name)
        try:
            await self._cleanup_hub(name)
            del self._hubs[name]
            logger.info(
                f"Unregistered hub {name}",
                extra={"hub": name},
            )
        except Exception as e:
            raise HubError(
                f"Failed to unregister hub: {e}",
                hub=name,
            )

    async def watch(
        self,
        hub_name: str,
        path: str,
        callback: Any,
    ) -> None:
        """Watch a file or directory for changes.

        Args:
            hub_name: Hub name
            path: Path to watch
            callback: Callback to invoke on changes

        Raises:
            HubNotFoundError: If hub is not found
            HubError: If watch setup fails

        """
        hub = await self.get(hub_name)
        if not hub.config.root_dir:
            raise HubError(
                "Hub does not support file watching",
                hub=hub_name,
            )

        try:
            # TODO: Implement file watching
            # For now, just store the callback
            self._watchers.setdefault(hub_name, set())
            task = asyncio.create_task(self._watch_path(hub, path, callback))
            self._watchers[hub_name].add(task)
            logger.info(
                f"Started watching {path} in hub {hub_name}",
                extra={
                    "hub": hub_name,
                    "path": path,
                },
            )
        except Exception as e:
            raise HubError(
                f"Failed to set up file watching: {e}",
                hub=hub_name,
            )

    async def _load_hubs(self) -> None:
        """Load hubs from the root directory.

        Raises:
            HubValidationError: If hub loading fails

        """
        if not self.root_dir:
            return

        try:
            # TODO: Implement hub loading from files
            pass
        except Exception as e:
            raise HubValidationError(
                f"Failed to load hubs: {e}",
                hub="manager",
            )

    async def _cleanup_hub(self, name: str) -> None:
        """Clean up a hub's resources.

        Args:
            name: Hub name

        Raises:
            HubError: If cleanup fails

        """
        hub = self._hubs.get(name)
        if not hub:
            return

        try:
            # Cancel any watchers
            if name in self._watchers:
                for task in self._watchers[name]:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                del self._watchers[name]

            # Clean up hub
            await hub.cleanup()
        except Exception as e:
            raise HubError(
                f"Failed to clean up hub: {e}",
                hub=name,
            )

    async def _watch_path(
        self,
        hub: Hub,
        path: str,
        callback: Any,
    ) -> None:
        """Watch a path for changes.

        Args:
            hub: Hub instance
            path: Path to watch
            callback: Callback to invoke on changes

        """
        try:
            while True:
                # TODO: Implement proper file watching
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info(
                f"Stopped watching {path} in hub {hub.name}",
                extra={
                    "hub": hub.name,
                    "path": path,
                },
            )
