"""Base algorithm implementation for dynamic sources."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ....common.errors import PepperpyError
from ....core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class AlgorithmError(PepperpyError):
    """Algorithm error."""
    pass


class Algorithm(Protocol):
    """Dynamic source algorithm protocol."""
    
    async def process(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Process data using algorithm.
        
        Args:
            data: Data to process
            context: Optional processing context
            
        Returns:
            Processed data
            
        Raises:
            AlgorithmError: If data cannot be processed
        """
        ...


A = TypeVar("A", bound=Algorithm)


class BaseAlgorithm(Lifecycle):
    """Base algorithm implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm.
        
        Args:
            name: Algorithm name
            config: Optional algorithm configuration
        """
        super().__init__(name)
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return algorithm configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize algorithm."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up algorithm."""
        pass
        
    async def process(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Process data using algorithm.
        
        Args:
            data: Data to process
            context: Optional processing context
            
        Returns:
            Processed data
            
        Raises:
            AlgorithmError: If data cannot be processed
        """
        try:
            # Validate input
            self._validate_input(data)
            
            # Process data
            result = await self._process_data(data, context)
            
            # Validate output
            self._validate_output(result)
            
            return result
            
        except Exception as e:
            raise AlgorithmError(f"Failed to process data: {e}") from e
            
    async def _process_data(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Process data using algorithm implementation.
        
        Args:
            data: Data to process
            context: Optional processing context
            
        Returns:
            Processed data
            
        Raises:
            AlgorithmError: If data cannot be processed
        """
        raise NotImplementedError("Subclasses must implement _process_data()")
        
    def _validate_input(self, data: Any) -> None:
        """Validate input data.
        
        Args:
            data: Data to validate
            
        Raises:
            AlgorithmError: If data is invalid
        """
        pass
        
    def _validate_output(self, data: Any) -> None:
        """Validate output data.
        
        Args:
            data: Data to validate
            
        Raises:
            AlgorithmError: If data is invalid
        """
        pass
        
    def validate(self) -> None:
        """Validate algorithm state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Algorithm name cannot be empty")


class AlgorithmChain(BaseAlgorithm):
    """Algorithm chain implementation."""
    
    def __init__(
        self,
        name: str,
        algorithms: List[Algorithm],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm chain.
        
        Args:
            name: Chain name
            algorithms: Algorithms to chain
            config: Optional chain configuration
        """
        super().__init__(name, config)
        self._algorithms = algorithms
        
    async def _process_data(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Process data using chained algorithms.
        
        Args:
            data: Data to process
            context: Optional processing context
            
        Returns:
            Processed data
            
        Raises:
            AlgorithmError: If data cannot be processed
        """
        try:
            # Process data through chain
            result = data
            for algorithm in self._algorithms:
                result = await algorithm.process(result, context)
                
            return result
            
        except Exception as e:
            raise AlgorithmError(f"Failed to process data: {e}") from e
            
    def validate(self) -> None:
        """Validate chain state."""
        super().validate()
        
        if not self._algorithms:
            raise ValueError("No algorithms provided")
