"""Types module for Pepperpy."""

from .base import (
    PepperpyObject,
    DictInitializable,
    Cloneable,
    Validatable,
    Serializable,
    Equatable,
    Comparable,
    Stringable,
    ContextManageable,
    Disposable,
)
from .data import (
    Embeddable,
    Chunkable,
    SimilarityComparable,
    Mergeable,
    Storable,
    Indexable,
    Cacheable,
    Versionable,
)
from .models import (
    Model,
    TextGenerator,
    EmbeddingGenerator,
    Trainable,
    Tokenizer,
    ModelConfig,
)
from .learning import (
    Example,
    ExampleStore,
    LearningStrategy,
    LearningWorkflow,
    LearningMetrics,
)
from .storage import (
    StorageBackend,
    VectorStore,
    DocumentStore,
    MemoryStore,
    Cache,
)

# Type variables
from .base import T, K, V
from .data import T as DataT, D
from .models import T as ModelT, M
from .learning import T as LearningT, E
from .storage import T as StorageT

__all__ = [
    # Base types
    "PepperpyObject",
    "DictInitializable",
    "Cloneable",
    "Validatable",
    "Serializable",
    "Equatable",
    "Comparable",
    "Stringable",
    "ContextManageable",
    "Disposable",
    # Data types
    "Embeddable",
    "Chunkable",
    "SimilarityComparable",
    "Mergeable",
    "Storable",
    "Indexable",
    "Cacheable",
    "Versionable",
    # Model types
    "Model",
    "TextGenerator",
    "EmbeddingGenerator",
    "Trainable",
    "Tokenizer",
    "ModelConfig",
    # Learning types
    "Example",
    "ExampleStore",
    "LearningStrategy",
    "LearningWorkflow",
    "LearningMetrics",
    # Storage types
    "StorageBackend",
    "VectorStore",
    "DocumentStore",
    "MemoryStore",
    "Cache",
    # Type variables
    "T",
    "K",
    "V",
    "DataT",
    "D",
    "ModelT",
    "M",
    "LearningT",
    "E",
    "StorageT",
]
