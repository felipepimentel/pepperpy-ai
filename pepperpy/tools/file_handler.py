"""File handler implementation.

This module provides functionality for handling file operations,
including reading, writing, and validation.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.events import Event, EventBus
from pepperpy.monitoring import Monitor
from pepperpy.security import Validator


class FileError(PepperpyError):
    """File error."""
    pass


class FileHandler(Lifecycle):
    """File handler implementation."""
    
    def __init__(
        self,
        name: str,
        base_path: Union[str, Path],
        allowed_extensions: Optional[Set[str]] = None,
        max_size: Optional[int] = None,
        event_bus: Optional[EventBus] = None,
        monitor: Optional[Monitor] = None,
        validator: Optional[Validator] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize handler.
        
        Args:
            name: Handler name
            base_path: Base path for file operations
            allowed_extensions: Optional set of allowed file extensions
            max_size: Optional maximum file size in bytes
            event_bus: Optional event bus
            monitor: Optional monitor
            validator: Optional validator
            config: Optional configuration
        """
        super().__init__()
        self.name = name
        self._base_path = Path(base_path)
        self._allowed_extensions = allowed_extensions
        self._max_size = max_size
        self._event_bus = event_bus
        self._monitor = monitor
        self._validator = validator
        self._config = config or {}
        
    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate file path.
        
        Args:
            path: File path
            
        Returns:
            Validated path
            
        Raises:
            FileError: If path is invalid
        """
        try:
            path = Path(path)
            if not path.is_absolute():
                path = self._base_path / path
                
            path = path.resolve()
            
            if not str(path).startswith(str(self._base_path)):
                raise FileError("Path outside base directory")
                
            return path
        except Exception as e:
            raise FileError(f"Invalid path: {e}")
            
    def _validate_extension(self, path: Path) -> None:
        """Validate file extension.
        
        Args:
            path: File path
            
        Raises:
            FileError: If extension not allowed
        """
        if not self._allowed_extensions:
            return
            
        ext = path.suffix.lower()
        if ext not in self._allowed_extensions:
            raise FileError(f"Extension not allowed: {ext}")
            
    def _validate_size(self, size: int) -> None:
        """Validate file size.
        
        Args:
            size: File size in bytes
            
        Raises:
            FileError: If size exceeds maximum
        """
        if not self._max_size:
            return
            
        if size > self._max_size:
            raise FileError(
                f"File size exceeds maximum: {size} > {self._max_size}"
            )
            
    async def read_file(self, path: Union[str, Path]) -> bytes:
        """Read file.
        
        Args:
            path: File path
            
        Returns:
            File contents
            
        Raises:
            FileError: If read fails
        """
        path = self._validate_path(path)
        self._validate_extension(path)
        
        try:
            if not path.is_file():
                raise FileError("File not found")
                
            size = path.stat().st_size
            self._validate_size(size)
            
            contents = path.read_bytes()
            
            if self._validator:
                try:
                    self._validator.validate(contents)
                except Exception as e:
                    raise FileError(f"File validation failed: {e}")
                    
            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type="file_read",
                        source=self.name,
                        timestamp=datetime.now(),
                        data={
                            "path": str(path),
                            "size": size,
                        },
                    )
                )
                
            return contents
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"File read failed: {e}")
            
    async def write_file(
        self,
        path: Union[str, Path],
        contents: bytes,
    ) -> None:
        """Write file.
        
        Args:
            path: File path
            contents: File contents
            
        Raises:
            FileError: If write fails
        """
        path = self._validate_path(path)
        self._validate_extension(path)
        self._validate_size(len(contents))
        
        try:
            if self._validator:
                try:
                    self._validator.validate(contents)
                except Exception as e:
                    raise FileError(f"File validation failed: {e}")
                    
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
            
            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type="file_written",
                        source=self.name,
                        timestamp=datetime.now(),
                        data={
                            "path": str(path),
                            "size": len(contents),
                        },
                    )
                )
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"File write failed: {e}")
            
    async def delete_file(self, path: Union[str, Path]) -> None:
        """Delete file.
        
        Args:
            path: File path
            
        Raises:
            FileError: If deletion fails
        """
        path = self._validate_path(path)
        
        try:
            if not path.is_file():
                raise FileError("File not found")
                
            path.unlink()
            
            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type="file_deleted",
                        source=self.name,
                        timestamp=datetime.now(),
                        data={"path": str(path)},
                    )
                )
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"File deletion failed: {e}")
            
    async def list_files(
        self,
        path: Union[str, Path] = ".",
        recursive: bool = False,
    ) -> List[Path]:
        """List files.
        
        Args:
            path: Directory path
            recursive: Whether to list recursively
            
        Returns:
            List of file paths
            
        Raises:
            FileError: If listing fails
        """
        path = self._validate_path(path)
        
        try:
            if not path.is_dir():
                raise FileError("Directory not found")
                
            if recursive:
                files = [
                    p for p in path.rglob("*")
                    if p.is_file()
                    and (
                        not self._allowed_extensions
                        or p.suffix.lower() in self._allowed_extensions
                    )
                ]
            else:
                files = [
                    p for p in path.iterdir()
                    if p.is_file()
                    and (
                        not self._allowed_extensions
                        or p.suffix.lower() in self._allowed_extensions
                    )
                ]
                
            if self._event_bus:
                await self._event_bus.publish(
                    Event(
                        type="files_listed",
                        source=self.name,
                        timestamp=datetime.now(),
                        data={
                            "path": str(path),
                            "recursive": recursive,
                            "count": len(files),
                        },
                    )
                )
                
            return files
        except FileError:
            raise
        except Exception as e:
            raise FileError(f"File listing failed: {e}")
            
    async def _initialize(self) -> None:
        """Initialize handler."""
        if not self._base_path.is_dir():
            raise FileError("Base directory not found")
            
        if self._event_bus:
            await self._event_bus.initialize()
            
        if self._monitor:
            await self._monitor.initialize()
            
        if self._validator:
            await self._validator.initialize()
            
    async def _cleanup(self) -> None:
        """Clean up handler."""
        if self._validator:
            await self._validator.cleanup()
            
        if self._monitor:
            await self._monitor.cleanup()
            
        if self._event_bus:
            await self._event_bus.cleanup()
            
    def validate(self) -> None:
        """Validate handler state."""
        super().validate()
        
        if not self.name:
            raise FileError("Empty handler name")
            
        if not self._base_path:
            raise FileError("Empty base path")
            
        if self._max_size is not None and self._max_size <= 0:
            raise FileError("Invalid maximum file size")
            
        if self._event_bus:
            self._event_bus.validate()
            
        if self._monitor:
            self._monitor.validate()
            
        if self._validator:
            self._validator.validate() 