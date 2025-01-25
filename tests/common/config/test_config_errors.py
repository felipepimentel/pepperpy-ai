"""Tests for configuration error handling."""

from pathlib import Path
import pytest
import yaml

from pepperpy.core.config import (
    BaseConfig,
    ConfigError,
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


def test_base_config_invalid_yaml():
    """Test base config with invalid YAML."""
    with pytest.raises(ConfigError):
        BaseConfig.from_yaml("invalid: yaml: content", name="test")


def test_base_config_invalid_dict():
    """Test base config with invalid dictionary."""
    with pytest.raises(ConfigError):
        BaseConfig.from_dict({"invalid": "dict"}, name="test")


def test_vector_store_config_invalid_dimension():
    """Test vector store config with invalid dimension."""
    with pytest.raises(ConfigError):
        VectorStoreConfig(name="test", dimension=-1)


def test_vector_store_config_missing_index_path():
    """Test vector store config with missing index path."""
    with pytest.raises(ConfigError):
        VectorStoreConfig(name="test", dimension=512, metric="cosine")


def test_document_store_config_invalid_chunk_size():
    """Test document store config with invalid chunk size."""
    with pytest.raises(ConfigError):
        DocumentStoreConfig(name="test", chunk_size=-1)


def test_document_store_config_invalid_overlap():
    """Test document store config with invalid overlap."""
    with pytest.raises(ConfigError):
        DocumentStoreConfig(name="test", chunk_size=1000, overlap=-1)


def test_memory_store_config_invalid_max_size():
    """Test memory store config with invalid max size."""
    with pytest.raises(ConfigError):
        MemoryStoreConfig(name="test", short_term_max_size=-1)


def test_memory_store_config_invalid_ttl():
    """Test memory store config with invalid TTL."""
    with pytest.raises(ConfigError):
        MemoryStoreConfig(name="test", short_term_max_size=1000, short_term_ttl_seconds=-1)


def test_openai_config_invalid_temperature():
    """Test OpenAI config with invalid temperature."""
    with pytest.raises(ConfigError):
        OpenAIConfig(name="test", temperature=2.0)


def test_openai_config_invalid_max_tokens():
    """Test OpenAI config with invalid max tokens."""
    with pytest.raises(ConfigError):
        OpenAIConfig(name="test", max_tokens=-1)


def test_anthropic_config_invalid_temperature():
    """Test Anthropic config with invalid temperature."""
    with pytest.raises(ConfigError):
        AnthropicConfig(name="test", temperature=2.0)


def test_anthropic_config_invalid_top_k():
    """Test Anthropic config with invalid top k."""
    with pytest.raises(ConfigError):
        AnthropicConfig(name="test", top_k=-1)


def test_rag_config_invalid_context_length():
    """Test RAG config with invalid context length."""
    with pytest.raises(ConfigError):
        RAGConfig(name="test", max_context_length=-1)


def test_rag_config_invalid_similarity():
    """Test RAG config with invalid similarity threshold."""
    with pytest.raises(ConfigError):
        RAGConfig(name="test", min_similarity=2.0)


def test_in_context_config_invalid_examples():
    """Test in-context config with invalid max examples."""
    with pytest.raises(ConfigError):
        InContextConfig(name="test", max_examples=-1)


def test_in_context_config_invalid_threshold():
    """Test in-context config with invalid similarity threshold."""
    with pytest.raises(ConfigError):
        InContextConfig(name="test", similarity_threshold=2.0)


def test_retrieval_config_invalid_context_length():
    """Test retrieval config with invalid context length."""
    with pytest.raises(ConfigError):
        RetrievalConfig(name="test", max_context_length=-1)


def test_retrieval_config_invalid_similarity():
    """Test retrieval config with invalid similarity threshold."""
    with pytest.raises(ConfigError):
        RetrievalConfig(name="test", min_similarity=2.0)


def test_fine_tuning_config_invalid_epochs():
    """Test fine-tuning config with invalid epochs."""
    with pytest.raises(ConfigError):
        FineTuningConfig(name="test", num_epochs=-1)


def test_fine_tuning_config_invalid_learning_rate():
    """Test fine-tuning config with invalid learning rate."""
    with pytest.raises(ConfigError):
        FineTuningConfig(name="test", learning_rate=-1.0)


def test_metrics_config_invalid_buffer_size():
    """Test metrics config with invalid buffer size."""
    with pytest.raises(ConfigError):
        MetricsConfig(name="test", buffer_size=-1)


def test_logging_config_invalid_format():
    """Test logging config with invalid format string."""
    with pytest.raises(ConfigError):
        LoggingConfig(name="test", format="")


def test_data_stores_config_invalid_component():
    """Test data stores config with invalid component."""
    vector_store = VectorStoreConfig(name="test", dimension=512)
    with pytest.raises(ConfigError):
        DataStoresConfig(name="test", vector_store=vector_store)


def test_llm_config_invalid_component():
    """Test LLM config with invalid component."""
    openai = OpenAIConfig(name="test", temperature=0.7)
    with pytest.raises(ConfigError):
        LLMConfig(name="test", openai=openai)


def test_learning_config_invalid_component():
    """Test learning config with invalid component."""
    rag = RAGConfig(name="test", max_context_length=4000)
    with pytest.raises(ConfigError):
        LearningConfig(name="test", rag=rag)


def test_monitoring_config_invalid_component():
    """Test monitoring config with invalid component."""
    metrics = MetricsConfig(name="test", buffer_size=100)
    with pytest.raises(ConfigError):
        MonitoringConfig(name="test", metrics=metrics) 