"""Learning constants for Pepperpy."""

from enum import Enum
from typing import Final

# Learning strategy types
class StrategyType(str, Enum):
    """Learning strategy types."""
    
    IN_CONTEXT = "in_context"
    RETRIEVAL = "retrieval"
    FINE_TUNING = "fine_tuning"
    HYBRID = "hybrid"
    ENSEMBLE = "ensemble"
    ACTIVE = "active"
    REINFORCEMENT = "reinforcement"

# Example types
class ExampleType(str, Enum):
    """Example types."""
    
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    SYNTHETIC = "synthetic"
    HUMAN = "human"
    GENERATED = "generated"

# Workflow types
class WorkflowType(str, Enum):
    """Workflow types."""
    
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    ADAPTIVE = "adaptive"

# Metric types
class MetricType(str, Enum):
    """Metric types."""
    
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    BLEU = "bleu"
    ROUGE = "rouge"
    METEOR = "meteor"
    PERPLEXITY = "perplexity"
    LATENCY = "latency"
    COST = "cost"

# Default learning settings
DEFAULT_NUM_EXAMPLES: Final[int] = 5
DEFAULT_SIMILARITY_THRESHOLD: Final[float] = 0.7
DEFAULT_MAX_EXAMPLES: Final[int] = 10
DEFAULT_NUM_EPOCHS: Final[int] = 3
DEFAULT_LEARNING_RATE: Final[float] = 2e-5
DEFAULT_BATCH_SIZE: Final[int] = 4
DEFAULT_VALIDATION_SPLIT: Final[float] = 0.2
DEFAULT_MAX_STEPS: Final[int] = 1000
DEFAULT_PATIENCE: Final[int] = 3

# Learning phases
class LearningPhase(str, Enum):
    """Learning phases."""
    
    PREPARATION = "preparation"
    TRAINING = "training"
    VALIDATION = "validation"
    TESTING = "testing"
    INFERENCE = "inference"
    FEEDBACK = "feedback"
    ADAPTATION = "adaptation"

# Example sources
class ExampleSource(str, Enum):
    """Example sources."""
    
    USER = "user"
    SYSTEM = "system"
    EXTERNAL = "external"
    GENERATED = "generated"
    SYNTHETIC = "synthetic"
    CURATED = "curated"

# Learning modes
class LearningMode(str, Enum):
    """Learning modes."""
    
    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"
    CONTINUOUS = "continuous"
    BATCH = "batch"
    INTERACTIVE = "interactive"

# Feedback types
class FeedbackType(str, Enum):
    """Feedback types."""
    
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    REWARD = "reward"
    CORRECTION = "correction"
    PREFERENCE = "preference"
    RANKING = "ranking" 