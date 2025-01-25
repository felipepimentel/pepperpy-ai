"""Tests for loading default configuration."""

from pathlib import Path
import pytest
import yaml
from typing import Dict, Any, List

from pepperpy.core.config import (
    DataStoresConfig,
    VectorStoreConfig,
    DocumentStoreConfig,
    MemoryStoreConfig,
    LLMConfig,
    OpenAIConfig,
    AnthropicConfig,
    RAGConfig,
    LearningConfig,
    InContextConfig,
    RetrievalConfig,
    FineTuningConfig,
    MonitoringConfig,
    MetricsConfig,
    LoggingConfig,
    ConfigError,
)


@pytest.fixture
def default_config_path():
    """Get path to default configuration file."""
    return Path("pepperpy/common/config/default_config.yaml")


@pytest.fixture
def config_dict(default_config_path):
    """Load configuration dictionary from YAML."""
    with open(default_config_path) as f:
        return yaml.safe_load(f)


def validate_config_section(config: Dict[str, Any], section: str, required_fields: List[str]) -> None:
    """Validate configuration section has required fields.
    
    Args:
        config: Configuration dictionary
        section: Section name
        required_fields: List of required field names
        
    Raises:
        ConfigError: If validation fails
    """
    if section not in config:
        raise ConfigError(f"Missing required section: {section}")
        
    section_config = config[section]
    missing_fields = [field for field in required_fields if field not in section_config]
    if missing_fields:
        raise ConfigError(f"Missing required fields in {section}: {missing_fields}")


def test_load_default_data_stores_config(config_dict):
    """Test loading default data stores configuration."""
    # Validate required sections and fields
    validate_config_section(config_dict, "vector_store", ["dimension", "metric", "type", "index_path"])
    validate_config_section(config_dict, "document_store", ["chunk_size", "chunk_overlap", "type", "storage_path"])
    validate_config_section(config_dict, "memory_store", ["type", "short_term", "long_term"])
    
    vector_store = VectorStoreConfig(
        name="vector_store",
        dimension=config_dict["vector_store"]["dimension"],
        metric=config_dict["vector_store"]["metric"],
        type=config_dict["vector_store"]["type"],
        index_path=Path(config_dict["vector_store"]["index_path"]),
    )
    
    document_store = DocumentStoreConfig(
        name="document_store",
        chunk_size=config_dict["document_store"]["chunk_size"],
        overlap=config_dict["document_store"]["chunk_overlap"],
        type=config_dict["document_store"]["type"],
        storage_path=Path(config_dict["document_store"]["storage_path"]),
    )
    
    memory_store = MemoryStoreConfig(
        name="memory_store",
        short_term_max_size=config_dict["memory_store"]["short_term"]["max_size"],
        short_term_ttl_seconds=config_dict["memory_store"]["short_term"]["ttl_seconds"],
        long_term_storage_path=Path(config_dict["memory_store"]["long_term"]["storage_path"]),
        long_term_max_size=config_dict["memory_store"]["long_term"]["max_size"],
        type=config_dict["memory_store"]["type"],
    )
    
    config = DataStoresConfig(
        name="data_stores",
        vector_store=vector_store,
        document_store=document_store,
        memory_store=memory_store,
    )
    
    # Test vector store config
    assert config.vector_store is not None
    assert config.vector_store.type == "faiss"
    assert config.vector_store.dimension == 1536
    assert config.vector_store.metric == "cosine"
    assert config.vector_store.index_path == Path("data/vector_store")
    
    # Test document store config
    assert config.document_store is not None
    assert config.document_store.type == "file"
    assert config.document_store.storage_path == Path("data/documents")
    assert config.document_store.chunk_size == 1000
    assert config.document_store.overlap == 200
    
    # Test memory store config
    assert config.memory_store is not None
    assert config.memory_store.type == "hybrid"
    assert config.memory_store.short_term_max_size == 1000
    assert config.memory_store.short_term_ttl_seconds == 3600
    assert config.memory_store.long_term_storage_path == Path("data/memories")
    assert config.memory_store.long_term_max_size == 10000


def test_load_default_llm_config(config_dict):
    """Test loading default LLM configuration."""
    # Validate required sections and fields
    validate_config_section(config_dict, "llm", ["model", "temperature", "max_tokens", "default_provider", "providers"])
    validate_config_section(config_dict["llm"]["providers"], "openai", ["model", "temperature", "max_tokens"])
    validate_config_section(config_dict["llm"]["providers"], "anthropic", ["model", "temperature", "max_tokens"])
    
    openai = OpenAIConfig(
        name="openai",
        model=config_dict["llm"]["providers"]["openai"]["model"],
        temperature=config_dict["llm"]["providers"]["openai"]["temperature"],
        max_tokens=config_dict["llm"]["providers"]["openai"]["max_tokens"],
    )
    
    anthropic = AnthropicConfig(
        name="anthropic",
        model=config_dict["llm"]["providers"]["anthropic"]["model"],
        temperature=config_dict["llm"]["providers"]["anthropic"]["temperature"],
        max_tokens=config_dict["llm"]["providers"]["anthropic"]["max_tokens"],
    )
    
    config = LLMConfig(
        name="llm",
        model=config_dict["llm"]["model"],
        temperature=config_dict["llm"]["temperature"],
        max_tokens=config_dict["llm"]["max_tokens"],
        default_provider=config_dict["llm"]["default_provider"],
        openai=openai,
        anthropic=anthropic,
    )
    
    assert config.default_provider == "openai"
    
    # Test OpenAI config
    assert config.openai is not None
    assert config.openai.model == "gpt-4"
    assert config.openai.temperature == 0.7
    assert config.openai.max_tokens == 2000
    
    # Test Anthropic config
    assert config.anthropic is not None
    assert config.anthropic.model == "claude-2"
    assert config.anthropic.temperature == 0.7
    assert config.anthropic.max_tokens == 2000


def test_load_default_rag_config(default_config_path):
    """Test loading default RAG configuration."""
    with open(default_config_path) as f:
        config_dict = yaml.safe_load(f)
    
    config = RAGConfig(
        name="rag",
        max_context_length=config_dict["rag"]["max_context_length"],
        min_similarity=config_dict["rag"]["min_similarity"],
        batch_size=config_dict["rag"]["batch_size"],
        enable_metrics=config_dict["rag"]["enable_metrics"],
    )
    
    assert config.max_context_length == 4000
    assert config.min_similarity == 0.7
    assert config.batch_size == 5
    assert config.enable_metrics is True


def test_load_default_learning_config(config_dict):
    """Test loading default learning configuration."""
    # Validate required sections and fields
    validate_config_section(config_dict, "learning", ["strategies"])
    validate_config_section(config_dict["learning"]["strategies"], "in_context", ["max_examples", "similarity_threshold"])
    validate_config_section(config_dict["learning"]["strategies"], "retrieval", ["max_context_length", "min_similarity"])
    validate_config_section(config_dict["learning"]["strategies"], "fine_tuning", ["num_epochs", "batch_size", "learning_rate", "validation_split"])
    
    in_context = InContextConfig(
        name="in_context",
        max_examples=config_dict["learning"]["strategies"]["in_context"]["max_examples"],
        similarity_threshold=config_dict["learning"]["strategies"]["in_context"]["similarity_threshold"],
    )
    
    retrieval = RetrievalConfig(
        name="retrieval",
        max_context_length=config_dict["learning"]["strategies"]["retrieval"]["max_context_length"],
        min_similarity=config_dict["learning"]["strategies"]["retrieval"]["min_similarity"],
    )
    
    fine_tuning = FineTuningConfig(
        name="fine_tuning",
        num_epochs=config_dict["learning"]["strategies"]["fine_tuning"]["num_epochs"],
        batch_size=config_dict["learning"]["strategies"]["fine_tuning"]["batch_size"],
        learning_rate=config_dict["learning"]["strategies"]["fine_tuning"]["learning_rate"],
        validation_split=config_dict["learning"]["strategies"]["fine_tuning"]["validation_split"],
    )
    
    config = LearningConfig(
        name="learning",
        in_context=in_context,
        retrieval=retrieval,
        fine_tuning=fine_tuning,
    )
    
    # Test in-context config
    assert config.in_context is not None
    assert config.in_context.max_examples == 5
    assert config.in_context.similarity_threshold == 0.8
    
    # Test retrieval config
    assert config.retrieval is not None
    assert config.retrieval.max_context_length == 2000
    assert config.retrieval.min_similarity == 0.7
    
    # Test fine-tuning config
    assert config.fine_tuning is not None
    assert config.fine_tuning.num_epochs == 3
    assert config.fine_tuning.batch_size == 4
    assert config.fine_tuning.learning_rate == 2e-5
    assert config.fine_tuning.validation_split == 0.2


def test_load_default_monitoring_config(config_dict):
    """Test loading default monitoring configuration."""
    # Validate required sections and fields
    validate_config_section(config_dict, "monitoring", ["metrics", "logging"])
    validate_config_section(config_dict["monitoring"], "metrics", ["buffer_size", "output_path"])
    validate_config_section(config_dict["monitoring"], "logging", ["level", "format", "output_path"])
    
    metrics = MetricsConfig(
        name="metrics",
        buffer_size=config_dict["monitoring"]["metrics"]["buffer_size"],
        output_path=Path(config_dict["monitoring"]["metrics"]["output_path"]),
    )
    
    logging = LoggingConfig(
        name="logging",
        level=config_dict["monitoring"]["logging"]["level"],
        format=config_dict["monitoring"]["logging"]["format"],
        output_path=Path(config_dict["monitoring"]["logging"]["output_path"]),
    )
    
    config = MonitoringConfig(
        name="monitoring",
        metrics=metrics,
        logging=logging,
    )
    
    # Test metrics config
    assert config.metrics is not None
    assert config.metrics.output_path == Path("data/metrics")
    assert config.metrics.buffer_size == 100
    
    # Test logging config
    assert config.logging is not None
    assert config.logging.level == "INFO"
    assert config.logging.format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    assert config.logging.output_path == Path("logs/pepperpy.log")


def test_invalid_config_missing_section():
    """Test loading config with missing section."""
    invalid_config = {}
    with pytest.raises(ConfigError, match="Missing required section"):
        validate_config_section(invalid_config, "vector_store", ["dimension"])


def test_invalid_config_missing_fields():
    """Test loading config with missing fields."""
    invalid_config = {"vector_store": {}}
    with pytest.raises(ConfigError, match="Missing required fields"):
        validate_config_section(invalid_config, "vector_store", ["dimension"]) 