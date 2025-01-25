"""Configuration types for Pepperpy framework."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path

from .config import Config, ConfigError


@dataclass
class BaseConfig(Config):
    """Base configuration class."""
    config_path: Optional[str] = None

    @classmethod
    def from_yaml(cls, yaml_str: str, name: str) -> 'BaseConfig':
        """Create config from YAML string."""
        return cls(name=name)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], name: str) -> 'BaseConfig':
        """Create config from dictionary."""
        return cls(name=name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {"config_path": self.config_path}

    def save(self, path: Path) -> None:
        """Save config to file."""
        pass


@dataclass
class VectorStoreConfig(Config):
    """Vector store configuration."""
    dimension: int = 512
    metric: str = "cosine"
    type: str = "faiss"
    index_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.dimension <= 0:
            raise ConfigError("Dimension must be positive")


@dataclass
class DocumentStoreConfig(Config):
    """Document store configuration."""
    chunk_size: int = 1000
    overlap: int = 200
    type: str = "file"
    storage_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.chunk_size <= 0:
            raise ConfigError("Chunk size must be positive")
        if self.overlap < 0:
            raise ConfigError("Overlap must be non-negative")


@dataclass
class MemoryStoreConfig(Config):
    """Memory store configuration."""
    short_term_max_size: int = 1000
    long_term_max_size: int = 10000
    type: str = "hybrid"
    short_term_ttl_seconds: int = 3600
    long_term_storage_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.short_term_max_size <= 0:
            raise ConfigError("Short term max size must be positive")
        if self.short_term_ttl_seconds <= 0:
            raise ConfigError("Short term TTL must be positive")


@dataclass
class LLMConfig(Config):
    """Base LLM configuration."""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    default_provider: str = "openai"
    openai: Optional['OpenAIConfig'] = None
    anthropic: Optional['AnthropicConfig'] = None


@dataclass
class OpenAIConfig(LLMConfig):
    """OpenAI configuration."""
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if not 0 <= self.temperature <= 1:
            raise ConfigError("Temperature must be between 0 and 1")
        if self.max_tokens <= 0:
            raise ConfigError("Max tokens must be positive")


@dataclass
class AnthropicConfig(LLMConfig):
    """Anthropic configuration."""
    top_k: int = 50
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if not 0 <= self.temperature <= 1:
            raise ConfigError("Temperature must be between 0 and 1")
        if self.top_k <= 0:
            raise ConfigError("Top k must be positive")


@dataclass
class RAGConfig(Config):
    """RAG configuration."""
    max_context_length: int = 4000
    num_chunks: int = 5
    min_similarity: float = 0.7
    batch_size: int = 5
    enable_metrics: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.max_context_length <= 0:
            raise ConfigError("Max context length must be positive")
        if not 0 <= self.min_similarity <= 1:
            raise ConfigError("Min similarity must be between 0 and 1")


@dataclass
class InContextConfig(Config):
    """In-context learning configuration."""
    max_examples: int = 5
    similarity_threshold: float = 0.8
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.max_examples <= 0:
            raise ConfigError("Max examples must be positive")
        if not 0 <= self.similarity_threshold <= 1:
            raise ConfigError("Similarity threshold must be between 0 and 1")


@dataclass
class RetrievalConfig(Config):
    """Retrieval-based learning configuration."""
    max_context_length: int = 2000
    min_similarity: float = 0.7
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.max_context_length <= 0:
            raise ConfigError("Max context length must be positive")
        if not 0 <= self.min_similarity <= 1:
            raise ConfigError("Min similarity must be between 0 and 1")


@dataclass
class FineTuningConfig(Config):
    """Fine-tuning configuration."""
    num_epochs: int = 3
    batch_size: int = 32
    learning_rate: float = 2e-5
    validation_split: float = 0.2
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.num_epochs <= 0:
            raise ConfigError("Number of epochs must be positive")
        if self.learning_rate <= 0:
            raise ConfigError("Learning rate must be positive")


@dataclass
class MetricsConfig(Config):
    """Metrics configuration."""
    buffer_size: int = 100
    output_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if self.buffer_size <= 0:
            raise ConfigError("Buffer size must be positive")


@dataclass
class LoggingConfig(Config):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    output_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        super().__post_init__()
        if not self.format:
            raise ConfigError("Format string cannot be empty")


@dataclass
class DataStoresConfig(Config):
    """Data stores configuration."""
    vector_store: Optional[VectorStoreConfig] = None
    document_store: Optional[DocumentStoreConfig] = None
    memory_store: Optional[MemoryStoreConfig] = None


@dataclass
class LearningConfig(Config):
    """Learning strategies configuration."""
    rag: Optional[RAGConfig] = None
    in_context: Optional[InContextConfig] = None
    retrieval: Optional[RetrievalConfig] = None
    fine_tuning: Optional[FineTuningConfig] = None


@dataclass
class MonitoringConfig(Config):
    """Monitoring configuration."""
    metrics: Optional[MetricsConfig] = None
    logging: Optional[LoggingConfig] = None 