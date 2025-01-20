"""Tests for loading default configuration."""

from pathlib import Path
import pytest
import yaml

from pepperpy.common.config import (
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
)


@pytest.fixture
def default_config_path():
    """Get path to default configuration file."""
    return Path("pepperpy/common/config/default_config.yaml")


def test_load_default_data_stores_config(default_config_path):
    """Test loading default data stores configuration."""
    with open(default_config_path) as f:
        config_dict = yaml.safe_load(f)
    
    vector_store = VectorStoreConfig(
        type=config_dict["vector_store"]["type"],
        dimension=config_dict["vector_store"]["dimension"],
        metric=config_dict["vector_store"]["metric"],
        index_path=Path(config_dict["vector_store"]["index_path"]),
    )
    
    document_store = DocumentStoreConfig(
        type=config_dict["document_store"]["type"],
        storage_path=Path(config_dict["document_store"]["storage_path"]),
        chunk_size=config_dict["document_store"]["chunk_size"],
        chunk_overlap=config_dict["document_store"]["chunk_overlap"],
    )
    
    memory_store = MemoryStoreConfig(
        type=config_dict["memory_store"]["type"],
        short_term_max_size=config_dict["memory_store"]["short_term"]["max_size"],
        short_term_ttl_seconds=config_dict["memory_store"]["short_term"]["ttl_seconds"],
        long_term_storage_path=Path(config_dict["memory_store"]["long_term"]["storage_path"]),
        long_term_max_size=config_dict["memory_store"]["long_term"]["max_size"],
    )
    
    config = DataStoresConfig(
        vector_store=vector_store,
        document_store=document_store,
        memory_store=memory_store,
    )
    config.validate()
    
    assert config.vector_store.type == "faiss"
    assert config.vector_store.dimension == 1536
    assert config.vector_store.metric == "cosine"
    assert config.vector_store.index_path == Path("data/vector_store")
    
    assert config.document_store.type == "file"
    assert config.document_store.storage_path == Path("data/documents")
    assert config.document_store.chunk_size == 1000
    assert config.document_store.chunk_overlap == 200
    
    assert config.memory_store.type == "hybrid"
    assert config.memory_store.short_term_max_size == 1000
    assert config.memory_store.short_term_ttl_seconds == 3600
    assert config.memory_store.long_term_storage_path == Path("data/memories")
    assert config.memory_store.long_term_max_size == 10000


def test_load_default_llm_config(default_config_path):
    """Test loading default LLM configuration."""
    with open(default_config_path) as f:
        config_dict = yaml.safe_load(f)
    
    openai = OpenAIConfig(
        model=config_dict["llm"]["providers"]["openai"]["model"],
        temperature=config_dict["llm"]["providers"]["openai"]["temperature"],
        max_tokens=config_dict["llm"]["providers"]["openai"]["max_tokens"],
    )
    
    anthropic = AnthropicConfig(
        model=config_dict["llm"]["providers"]["anthropic"]["model"],
        temperature=config_dict["llm"]["providers"]["anthropic"]["temperature"],
        max_tokens=config_dict["llm"]["providers"]["anthropic"]["max_tokens"],
    )
    
    config = LLMConfig(
        default_provider=config_dict["llm"]["default_provider"],
        openai=openai,
        anthropic=anthropic,
    )
    config.validate()
    
    assert config.default_provider == "openai"
    
    assert config.openai.model == "gpt-4"
    assert config.openai.temperature == 0.7
    assert config.openai.max_tokens == 2000
    
    assert config.anthropic.model == "claude-2"
    assert config.anthropic.temperature == 0.7
    assert config.anthropic.max_tokens == 2000


def test_load_default_rag_config(default_config_path):
    """Test loading default RAG configuration."""
    with open(default_config_path) as f:
        config_dict = yaml.safe_load(f)
    
    config = RAGConfig(
        max_context_length=config_dict["rag"]["max_context_length"],
        min_similarity=config_dict["rag"]["min_similarity"],
        batch_size=config_dict["rag"]["batch_size"],
        enable_metrics=config_dict["rag"]["enable_metrics"],
    )
    config.validate()
    
    assert config.max_context_length == 4000
    assert config.min_similarity == 0.7
    assert config.batch_size == 5
    assert config.enable_metrics is True


def test_load_default_learning_config(default_config_path):
    """Test loading default learning configuration."""
    with open(default_config_path) as f:
        config_dict = yaml.safe_load(f)
    
    in_context = InContextConfig(
        max_examples=config_dict["learning"]["strategies"]["in_context"]["max_examples"],
        similarity_threshold=config_dict["learning"]["strategies"]["in_context"]["similarity_threshold"],
    )
    
    retrieval = RetrievalConfig(
        max_context_length=config_dict["learning"]["strategies"]["retrieval"]["max_context_length"],
        min_similarity=config_dict["learning"]["strategies"]["retrieval"]["min_similarity"],
    )
    
    fine_tuning = FineTuningConfig(
        num_epochs=config_dict["learning"]["strategies"]["fine_tuning"]["num_epochs"],
        batch_size=config_dict["learning"]["strategies"]["fine_tuning"]["batch_size"],
        learning_rate=config_dict["learning"]["strategies"]["fine_tuning"]["learning_rate"],
        validation_split=config_dict["learning"]["strategies"]["fine_tuning"]["validation_split"],
    )
    
    config = LearningConfig(
        in_context=in_context,
        retrieval=retrieval,
        fine_tuning=fine_tuning,
    )
    config.validate()
    
    assert config.in_context.max_examples == 5
    assert config.in_context.similarity_threshold == 0.8
    
    assert config.retrieval.max_context_length == 2000
    assert config.retrieval.min_similarity == 0.7
    
    assert config.fine_tuning.num_epochs == 3
    assert config.fine_tuning.batch_size == 4
    assert config.fine_tuning.learning_rate == 2e-5
    assert config.fine_tuning.validation_split == 0.2


def test_load_default_monitoring_config(default_config_path):
    """Test loading default monitoring configuration."""
    with open(default_config_path) as f:
        config_dict = yaml.safe_load(f)
    
    metrics = MetricsConfig(
        output_path=Path(config_dict["monitoring"]["metrics"]["output_path"]),
        buffer_size=config_dict["monitoring"]["metrics"]["buffer_size"],
    )
    
    logging = LoggingConfig(
        level=config_dict["monitoring"]["logging"]["level"],
        format=config_dict["monitoring"]["logging"]["format"],
        output_path=Path(config_dict["monitoring"]["logging"]["output_path"]),
    )
    
    config = MonitoringConfig(
        metrics=metrics,
        logging=logging,
    )
    config.validate()
    
    assert config.metrics.output_path == Path("data/metrics")
    assert config.metrics.buffer_size == 100
    
    assert config.logging.level == "INFO"
    assert config.logging.format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    assert config.logging.output_path == Path("logs/pepperpy.log") 