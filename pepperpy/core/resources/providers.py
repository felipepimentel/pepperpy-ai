"""Resource providers module.

This module implements specific resource providers:
- Memory providers (shared memory, memory mapped files)
- File providers (local files, remote storage)
- Network providers (TCP/IP, Unix sockets)
- Process providers (local processes, remote processes)
"""

from typing import Dict, List, Optional

from pepperpy.core.common.base import Lifecycle
from pepperpy.core.common.types import ComponentState
from pepperpy.monitoring import logger
from pepperpy.resources.base import Resource
from pepperpy.resources.base import ResourceConfig as ResourceConfig
from pepperpy.resources.types import (
    FileResource,
    FileResourceConfig,
    MemoryResource,
    MemoryResourceConfig,
    NetworkResource,
    NetworkResourceConfig,
    ProcessResource,
    ProcessResourceConfig,
)


class ResourceProvider(Lifecycle):
    """Base resource provider implementation.

    This class provides the base interface for resource providers.
    """

    def __init__(self) -> None:
        """Initialize resource provider."""
        super().__init__()
        self._resources: Dict[str, Resource] = {}
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize resource provider."""
        try:
            self._state = ComponentState.RUNNING
            logger.info(f"Resource provider {self.__class__.__name__} initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize resource provider: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resource provider."""
        try:
            # Clean up resources
            resources = list(self._resources.values())
            for resource in resources:
                try:
                    await resource.cleanup()
                except Exception as e:
                    logger.error(f"Failed to cleanup resource {resource.name}: {e}")

            self._resources.clear()
            self._state = ComponentState.UNREGISTERED
            logger.info(f"Resource provider {self.__class__.__name__} cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup resource provider: {e}")
            raise

    def get_resource(self, name: str) -> Optional[Resource]:
        """Get resource by name.

        Args:
            name: Resource name

        Returns:
            Resource if found, None otherwise
        """
        return self._resources.get(name)

    def get_all_resources(self) -> List[Resource]:
        """Get all resources.

        Returns:
            List of all resources
        """
        return list(self._resources.values())


class MemoryProvider(ResourceProvider):
    """Memory resource provider implementation.

    This class provides memory resources like shared memory
    and memory mapped files.
    """

    async def create_shared_memory(
        self, name: str, size: int, persistent: bool = False
    ) -> MemoryResource:
        """Create shared memory resource.

        Args:
            name: Resource name
            size: Memory size in bytes
            persistent: Whether memory should persist

        Returns:
            Shared memory resource
        """
        config = MemoryResourceConfig(
            name=name,
            type="shared_memory",
            size=size,
            persistent=persistent,
        )
        resource = MemoryResource(config)
        await resource.initialize()
        self._resources[name] = resource
        return resource


class FileProvider(ResourceProvider):
    """File resource provider implementation.

    This class provides file resources like local files
    and remote storage.
    """

    async def create_local_file(
        self,
        name: str,
        path: str,
        size: int = 0,
        mode: str = "r+b",
        persistent: bool = False,
    ) -> FileResource:
        """Create local file resource.

        Args:
            name: Resource name
            path: File path
            size: File size in bytes (0 for no limit)
            mode: File mode
            persistent: Whether file should persist

        Returns:
            Local file resource
        """
        config = FileResourceConfig(
            name=name,
            type="local_file",
            path=path,
            size=size,
            mode=mode,
            persistent=persistent,
        )
        resource = FileResource(config)
        await resource.initialize()
        self._resources[name] = resource
        return resource


class NetworkProvider(ResourceProvider):
    """Network resource provider implementation.

    This class provides network resources like TCP/IP
    and Unix sockets.
    """

    async def create_tcp_connection(
        self, name: str, host: str, port: int, size: int = 8192, timeout: float = 30.0
    ) -> NetworkResource:
        """Create TCP connection resource.

        Args:
            name: Resource name
            host: Host address
            port: Port number
            size: Buffer size in bytes
            timeout: Connection timeout in seconds

        Returns:
            TCP connection resource
        """
        config = NetworkResourceConfig(
            name=name,
            type="tcp_connection",
            host=host,
            port=port,
            size=size,
            timeout=timeout,
        )
        resource = NetworkResource(config)
        await resource.initialize()
        self._resources[name] = resource
        return resource


class ProcessProvider(ResourceProvider):
    """Process resource provider implementation.

    This class provides process resources like local processes
    and remote processes.
    """

    async def create_local_process(
        self,
        name: str,
        command: str,
        size: int = 0,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> ProcessResource:
        """Create local process resource.

        Args:
            name: Resource name
            command: Command to run
            size: Memory limit in bytes (0 for no limit)
            args: Command arguments
            env: Environment variables
            cwd: Working directory

        Returns:
            Local process resource
        """
        config = ProcessResourceConfig(
            name=name,
            type="local_process",
            command=command,
            size=size,
            args=args or [],
            env=env or {},
            cwd=cwd,
        )
        resource = ProcessResource(config)
        await resource.initialize()
        self._resources[name] = resource
        return resource
