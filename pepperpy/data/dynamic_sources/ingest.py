"""Data ingestion implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle
from .algorithms.base_algorithm import Algorithm


logger = logging.getLogger(__name__)


class IngestError(PepperpyError):
    """Ingest error."""
    pass


class Source(Protocol):
    """Data source protocol."""
    
    async def read(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Read data from source.
        
        Args:
            context: Optional read context
            
        Returns:
            Source data
            
        Raises:
            IngestError: If data cannot be read
        """
        ...


S = TypeVar("S", bound=Source)


class Sink(Protocol):
    """Data sink protocol."""
    
    async def write(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write data to sink.
        
        Args:
            data: Data to write
            context: Optional write context
            
        Raises:
            IngestError: If data cannot be written
        """
        ...


K = TypeVar("K", bound=Sink)


class IngestManager(Lifecycle):
    """Data ingestion manager implementation."""
    
    def __init__(
        self,
        name: str,
        source: Source,
        sink: Sink,
        algorithms: Optional[List[Algorithm]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ingestion manager.
        
        Args:
            name: Manager name
            source: Data source
            sink: Data sink
            algorithms: Optional processing algorithms
            config: Optional manager configuration
        """
        super().__init__(name)
        self._source = source
        self._sink = sink
        self._algorithms = algorithms or []
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return manager configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize manager."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up manager."""
        pass
        
    async def ingest(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Ingest data from source to sink.
        
        Args:
            context: Optional ingestion context
            
        Raises:
            IngestError: If data cannot be ingested
        """
        try:
            # Read from source
            data = await self._source.read(context)
            
            # Process data
            result = data
            for algorithm in self._algorithms:
                result = await algorithm.process(result, context)
                
            # Write to sink
            await self._sink.write(result, context)
            
        except Exception as e:
            raise IngestError(f"Failed to ingest data: {e}") from e
            
    def validate(self) -> None:
        """Validate manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Manager name cannot be empty")
            
        if not self._source:
            raise ValueError("Data source not provided")
            
        if not self._sink:
            raise ValueError("Data sink not provided")


class FileSource(Source):
    """File data source implementation."""
    
    def __init__(
        self,
        path: str,
        encoding: str = "utf-8",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize file source.
        
        Args:
            path: File path
            encoding: File encoding (default: utf-8)
            config: Optional source configuration
        """
        self._path = path
        self._encoding = encoding
        self._config = config or {}
        
    async def read(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Read data from file.
        
        Args:
            context: Optional read context
            
        Returns:
            File contents
            
        Raises:
            IngestError: If file cannot be read
        """
        try:
            with open(self._path, "r", encoding=self._encoding) as f:
                return f.read()
                
        except Exception as e:
            raise IngestError(f"Failed to read file: {e}") from e


class FileSink(Sink):
    """File data sink implementation."""
    
    def __init__(
        self,
        path: str,
        encoding: str = "utf-8",
        mode: str = "w",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize file sink.
        
        Args:
            path: File path
            encoding: File encoding (default: utf-8)
            mode: File mode (default: w)
            config: Optional sink configuration
        """
        self._path = path
        self._encoding = encoding
        self._mode = mode
        self._config = config or {}
        
    async def write(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write data to file.
        
        Args:
            data: Data to write
            context: Optional write context
            
        Raises:
            IngestError: If data cannot be written
        """
        try:
            with open(self._path, self._mode, encoding=self._encoding) as f:
                f.write(str(data))
                
        except Exception as e:
            raise IngestError(f"Failed to write file: {e}") from e
