"""Resource types module.

This module defines common resource types and their interfaces:
- Memory resources (buffers, caches)
- File resources (temporary files, persistent storage)
- Network resources (connections, sockets)
- Process resources (subprocesses, threads)
"""

import os
import socket
import subprocess
from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel, Field

from pepperpy.core.types import ComponentState as ComponentState
from pepperpy.monitoring import logger as logger
from pepperpy.resources.base import Resource, ResourceConfig

# Type variables
T = TypeVar("T", bound=Resource)


class MemoryResourceConfig(ResourceConfig):
    """Memory resource configuration.

    Attributes:
        size: Memory size in bytes
        persistent: Whether memory should persist between uses
    """

    size: int = Field(default=1024, description="Memory size in bytes")
    persistent: bool = Field(default=False, description="Whether memory should persist")


class MemoryResource(Resource):
    """Memory resource implementation.

    This class represents memory resources like buffers and caches.
    """

    config: MemoryResourceConfig

    def __init__(self, config: MemoryResourceConfig) -> None:
        """Initialize memory resource.

        Args:
            config: Memory resource configuration
        """
        super().__init__(config)
        self._data: Optional[bytearray] = None

    async def _do_allocate(self) -> None:
        """Allocate memory resource."""
        if not self._data:
            self._data = bytearray(self.config.size)

    async def _do_release(self) -> None:
        """Release memory resource."""
        if not self.config.persistent:
            self._data = None

    async def _do_use(self) -> None:
        """Use memory resource."""
        pass

    async def _do_stop_use(self) -> None:
        """Stop using memory resource."""
        pass

    def get_data(self) -> Optional[bytearray]:
        """Get memory data.

        Returns:
            Memory data if allocated, None otherwise
        """
        return self._data if self.is_allocated() else None

    def set_data(self, data: bytes, offset: int = 0) -> None:
        """Set memory data.

        Args:
            data: Data to write
            offset: Offset to write at

        Raises:
            ValueError: If not allocated or data too large
        """
        if not self.is_allocated():
            raise ValueError("Memory not allocated")
        if not self._data or offset + len(data) > self.config.size:
            raise ValueError("Data too large")
        self._data[offset : offset + len(data)] = data


class FileResourceConfig(ResourceConfig):
    """File resource configuration.

    Attributes:
        path: File path
        mode: File mode
        persistent: Whether file should persist between uses
        size: File size in bytes
    """

    path: str = Field(..., description="File path")
    mode: str = Field(default="r+b", description="File mode")
    persistent: bool = Field(default=False, description="Whether file should persist")
    size: int = Field(default=0, description="File size in bytes")


class FileResource(Resource):
    """File resource implementation.

    This class represents file resources like temporary files
    and persistent storage.
    """

    config: FileResourceConfig

    def __init__(self, config: FileResourceConfig) -> None:
        """Initialize file resource.

        Args:
            config: File resource configuration
        """
        super().__init__(config)
        self._file: Optional[Any] = None

    async def _do_allocate(self) -> None:
        """Allocate file resource."""
        if not self._file:
            self._file = open(self.config.path, self.config.mode)

    async def _do_release(self) -> None:
        """Release file resource."""
        if self._file:
            self._file.close()
            if not self.config.persistent:
                try:
                    os.remove(self.config.path)
                except FileNotFoundError:
                    pass
            self._file = None

    async def _do_use(self) -> None:
        """Use file resource."""
        pass

    async def _do_stop_use(self) -> None:
        """Stop using file resource."""
        pass

    def get_file(self) -> Optional[Any]:
        """Get file object.

        Returns:
            File object if allocated, None otherwise
        """
        return self._file if self.is_allocated() else None


class NetworkResourceConfig(ResourceConfig):
    """Network resource configuration.

    Attributes:
        host: Host address
        port: Port number
        timeout: Connection timeout in seconds
        size: Buffer size in bytes
    """

    host: str = Field(..., description="Host address")
    port: int = Field(..., description="Port number")
    timeout: float = Field(default=30.0, description="Connection timeout in seconds")
    size: int = Field(default=8192, description="Buffer size in bytes")


class NetworkResource(Resource):
    """Network resource implementation.

    This class represents network resources like connections
    and sockets.
    """

    config: NetworkResourceConfig

    def __init__(self, config: NetworkResourceConfig) -> None:
        """Initialize network resource.

        Args:
            config: Network resource configuration
        """
        super().__init__(config)
        self._connection: Optional[Any] = None

    async def _do_allocate(self) -> None:
        """Allocate network resource."""
        if not self._connection:
            self._connection = socket.create_connection(
                (self.config.host, self.config.port), timeout=self.config.timeout
            )

    async def _do_release(self) -> None:
        """Release network resource."""
        if self._connection:
            self._connection.close()
            self._connection = None

    async def _do_use(self) -> None:
        """Use network resource."""
        pass

    async def _do_stop_use(self) -> None:
        """Stop using network resource."""
        pass

    def get_connection(self) -> Optional[Any]:
        """Get network connection.

        Returns:
            Network connection if allocated, None otherwise
        """
        return self._connection if self.is_allocated() else None


class ProcessResourceConfig(ResourceConfig):
    """Process resource configuration.

    Attributes:
        command: Command to run
        args: Command arguments
        env: Environment variables
        cwd: Working directory
        size: Memory limit in bytes
    """

    command: str = Field(..., description="Command to run")
    args: list = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    cwd: Optional[str] = Field(default=None, description="Working directory")
    size: int = Field(default=0, description="Memory limit in bytes")


class ProcessResource(Resource):
    """Process resource implementation.

    This class represents process resources like subprocesses
    and threads.
    """

    config: ProcessResourceConfig

    def __init__(self, config: ProcessResourceConfig) -> None:
        """Initialize process resource.

        Args:
            config: Process resource configuration
        """
        super().__init__(config)
        self._process: Optional[Any] = None

    async def _do_allocate(self) -> None:
        """Allocate process resource."""
        if not self._process:
            self._process = subprocess.Popen(
                [self.config.command] + self.config.args,
                env=self.config.env,
                cwd=self.config.cwd,
            )

    async def _do_release(self) -> None:
        """Release process resource."""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    async def _do_use(self) -> None:
        """Use process resource."""
        pass

    async def _do_stop_use(self) -> None:
        """Stop using process resource."""
        pass

    def get_process(self) -> Optional[Any]:
        """Get process object.

        Returns:
            Process object if allocated, None otherwise
        """
        return self._process if self.is_allocated() else None
