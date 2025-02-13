"""Component watcher for hot-reloading configurations."""

import asyncio
import functools
import logging
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List

import yaml
from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ComponentWatcher:
    """Watches component configurations for changes and triggers callbacks."""

    def __init__(self, hub_path: Path):
        """Initialize the component watcher.

        Args:
            hub_path: Path to the hub directory containing component configs

        """
        self.hub_path = hub_path
        self.observer = Observer()
        self.watchers: List[FileSystemEventHandler] = []
        self.observer.start()

    async def watch_agent(
        self, name: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]
    ):
        """Watch an agent configuration for changes.

        Args:
            name: Name of the agent
            callback: Function to call when config changes

        """
        path = self.hub_path / "agents" / f"{name}.yaml"
        await self._watch_component(path, callback)

    async def watch_workflow(
        self, name: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]
    ):
        """Watch a workflow configuration for changes.

        Args:
            name: Name of the workflow
            callback: Function to call when config changes

        """
        path = self.hub_path / "workflows" / f"{name}.yaml"
        await self._watch_component(path, callback)

    async def watch_team(
        self, name: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]
    ):
        """Watch a team configuration for changes.

        Args:
            name: Name of the team
            callback: Function to call when config changes

        """
        path = self.hub_path / "teams" / f"{name}.yaml"
        await self._watch_component(path, callback)

    async def _watch_component(
        self,
        path: Path,
        callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]],
    ):
        """Watch a component configuration file for changes.

        Args:
            path: Path to the config file
            callback: Function to call when config changes

        """
        if not path.exists():
            logger.warning("Config file not found: %s", str(path))
            return

        class ConfigHandler(FileSystemEventHandler):
            async def _handle_change(self, config_path: Path):
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)
                    await callback(config)
                except Exception as exc:
                    logger.error("Error reloading config: %s", str(exc))

            def on_modified(self, event: FileModifiedEvent):
                if event.src_path == str(path):
                    asyncio.create_task(self._handle_change(path))

        handler = ConfigHandler()
        self.observer.schedule(handler, str(path.parent), recursive=False)
        self.watchers.append(handler)

        # Initial load
        try:
            with open(path) as f:
                config = yaml.safe_load(f)
            await callback(config)
        except Exception as exc:
            logger.error("Error loading initial config: %s", str(exc))

    async def stop(self):
        """Stop watching all components."""
        for handler in self.watchers:
            self.observer.unschedule(handler)
        self.watchers.clear()
        self.observer.stop()
        self.observer.join()


def watch_component(config_path: str):
    """Decorator to watch a component configuration and reload on changes.

    Args:
        config_path: Path to the config file to watch

    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create watcher
            watcher = ComponentWatcher(Path(config_path).parent)

            # Define callback
            async def callback(config: Dict[str, Any]):
                await func(*args, **kwargs)

            # Start watching
            await watcher._watch_component(Path(config_path), callback)

            try:
                # Run function
                return await func(*args, **kwargs)
            finally:
                # Stop watcher
                await watcher.stop()

        return wrapper

    return decorator
