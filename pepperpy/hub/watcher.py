"""Component watcher for hot-reloading configurations."""

import asyncio
import functools
import logging
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple

import yaml
from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch

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
        self.watchers: List[Tuple[FileSystemEventHandler, ObservedWatch]] = []
        self.observer.start()
        self._event_queue: asyncio.Queue[Tuple[Path, Callable]] = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._processed_events: Set[str] = set()

    async def start(self):
        """Start the event processing task."""
        if self._task is None:
            self._task = asyncio.create_task(self._process_events())

    async def _process_events(self):
        """Process file system events from the queue."""
        while True:
            try:
                path, callback = await self._event_queue.get()
                try:
                    # Generate a unique event key
                    event_key = f"{path}:{hash(callback)}"
                    if event_key in self._processed_events:
                        continue
                    self._processed_events.add(event_key)

                    logger.debug("Loading modified config: %s", str(path))
                    with open(path) as f:
                        config = yaml.safe_load(f)
                    logger.debug("Loaded config: %s", str(config))
                    await callback(config)
                except Exception as exc:
                    logger.error("Error reloading config: %s", str(exc))
                finally:
                    self._event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error processing events: %s", str(exc))

    async def watch_agent(
        self, name: str, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]
    ):
        """Watch an agent configuration for changes.

        Args:
            name: Name of the agent
            callback: Function to call when config changes

        """
        path = self.hub_path / "agents" / f"{name}.yaml"
        await self.start()
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
        await self.start()
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
        await self.start()
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
            def __init__(self, queue: asyncio.Queue, path: Path, callback: Callable):
                self.queue = queue
                self.path = path
                self.callback = callback

            def on_modified(self, event: FileModifiedEvent):
                logger.debug("File modified event: %s", str(event.src_path))
                if event.src_path == str(self.path):
                    logger.debug("Matched path: %s", str(self.path))
                    self.queue.put_nowait((self.path, self.callback))

        handler = ConfigHandler(self._event_queue, path, callback)
        watch = self.observer.schedule(handler, str(path.parent), recursive=False)
        self.watchers.append((handler, watch))

        # Initial load
        try:
            logger.debug("Loading initial config: %s", str(path))
            with open(path) as f:
                config = yaml.safe_load(f)
            logger.debug("Loaded initial config: %s", str(config))
            await callback(config)
        except Exception as exc:
            logger.error("Error loading initial config: %s", str(exc))

    async def stop(self):
        """Stop watching all components."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        for handler, watch in self.watchers:
            self.observer.unschedule(watch)
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

            try:
                # Start watching
                await watcher.start()
                await watcher._watch_component(Path(config_path), callback)
                # No need to run function here as it's already called in _watch_component
                return None
            finally:
                # Stop watcher
                await watcher.stop()

        return wrapper

    return decorator
