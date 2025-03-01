"""Type definitions for the embedding system."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

import numpy as np

class EmbeddingType(Enum):
    """Types of embedding models."""
    
    TEXT = auto()
    IMAGE = auto()
    AUDIO = auto()
    MULTIMODAL = auto()

class EmbeddingDimension(Enum):
    """Standard embedding dimensions."""
    
    SMALL = 384
    MEDIUM = 768
    LARGE = 1536
    XLARGE = 3072

@dataclass
class EmbeddingConfig:
    """Configuration for embedding providers."""
    
    provider: str
    model: str
    api_key: Optional[str] = None
    dimension: Optional[int] = None
    type: EmbeddingType = EmbeddingType.TEXT
    batch_size: Optional[int] = None
    options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""
    
    embedding: Union[np.ndarray, List[np.ndarray]]
    model: str
    dimension: int
    text_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
