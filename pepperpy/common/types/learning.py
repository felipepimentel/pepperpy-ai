"""Learning types for Pepperpy."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, runtime_checkable
from .base import Cloneable, Serializable, Validatable
from .data import Embeddable, SimilarityComparable

# Type variables for learning types
T = TypeVar("T")
E = TypeVar("E")

# Protocol for objects that can be used as examples
@runtime_checkable
class Example(Embeddable, SimilarityComparable, Protocol):
    """Protocol for objects that can be used as examples."""
    
    @property
    def input(self) -> str:
        """Return example input."""
        ...
        
    @property
    def output(self) -> str:
        """Return example output."""
        ...
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return example metadata."""
        ...

# Protocol for objects that can manage examples
@runtime_checkable
class ExampleStore(Protocol[E]):
    """Protocol for objects that can manage examples."""
    
    async def add(self, example: E) -> None:
        """Add example to store."""
        ...
        
    async def get(self, example_id: str) -> Optional[E]:
        """Get example by ID."""
        ...
        
    async def find_similar(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.7
    ) -> List[E]:
        """Find similar examples."""
        ...
        
    async def list(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[E]:
        """List examples."""
        ...

# Protocol for objects that can be used as learning strategies
@runtime_checkable
class LearningStrategy(Protocol[T]):
    """Protocol for objects that can be used as learning strategies."""
    
    async def prepare(
        self,
        context: Dict[str, Any]
    ) -> None:
        """Prepare strategy with context."""
        ...
        
    async def execute(
        self,
        input: T,
        **kwargs: Any
    ) -> T:
        """Execute strategy on input."""
        ...
        
    async def update(
        self,
        feedback: Dict[str, Any]
    ) -> None:
        """Update strategy with feedback."""
        ...

# Protocol for objects that can be used as learning workflows
@runtime_checkable
class LearningWorkflow(Protocol[T]):
    """Protocol for objects that can be used as learning workflows."""
    
    async def initialize(
        self,
        config: Dict[str, Any]
    ) -> None:
        """Initialize workflow with configuration."""
        ...
        
    async def process(
        self,
        input: T,
        **kwargs: Any
    ) -> T:
        """Process input through workflow."""
        ...
        
    async def evaluate(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate workflow performance."""
        ...

# Protocol for objects that can be used as learning metrics
@runtime_checkable
class LearningMetrics(Protocol):
    """Protocol for objects that can be used as learning metrics."""
    
    def calculate(
        self,
        predicted: Any,
        actual: Any
    ) -> float:
        """Calculate metric value."""
        ...
        
    @property
    def name(self) -> str:
        """Return metric name."""
        ...
        
    @property
    def higher_is_better(self) -> bool:
        """Return whether higher values are better."""
        ... 