"""Tests for configuration error handling."""

from pathlib import Path
import pytest
import yaml

from pepperpy.common.config import (
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
    """Test loading invalid YAML file."""
    with pytest.raises(ConfigError):
        BaseConfig.from_yaml(Path("nonexistent.yaml"))


def test_base_config_invalid_dict():
    """Test creating config from invalid dictionary."""
    with pytest.raises(ConfigError):
        BaseConfig.from_dict({"invalid_key": "value"})


def test_vector_store_config_invalid_dimension():
    """Test vector store config with invalid dimension."""
    with pytest.raises(ConfigError):
        VectorStoreConfig(dimension=-1).validate()


def test_vector_store_config_missing_index_path():
    """Test vector store config with missing index path."""
    with pytest.raises(ConfigError):
        VectorStoreConfig(type="faiss", index_path=None).validate()


def test_document_store_config_invalid_chunk_size():
    """Test document store config with invalid chunk size."""
    with pytest.raises(ConfigError):
        DocumentStoreConfig(chunk_size=-1).validate()


def test_document_store_config_invalid_overlap():
    """Test document store config with invalid chunk overlap."""
    with pytest.raises(ConfigError):
        DocumentStoreConfig(chunk_size=100, chunk_overlap=200).validate()


def test_memory_store_config_invalid_max_size():
    """Test memory store config with invalid max size."""
    with pytest.raises(ConfigError):
        MemoryStoreConfig(short_term_max_size=-1).validate()


def test_memory_store_config_invalid_ttl():
    """Test memory store config with invalid TTL."""
    with pytest.raises(ConfigError):
        MemoryStoreConfig(short_term_ttl_seconds=-1).validate()


def test_openai_config_invalid_temperature():
    """Test OpenAI config with invalid temperature."""
    with pytest.raises(ConfigError):
        OpenAIConfig(temperature=2.5).validate()


def test_openai_config_invalid_max_tokens():
    """Test OpenAI config with invalid max tokens."""
    with pytest.raises(ConfigError):
        OpenAIConfig(max_tokens=-1).validate()


def test_anthropic_config_invalid_temperature():
    """Test Anthropic config with invalid temperature."""
    with pytest.raises(ConfigError):
        AnthropicConfig(temperature=1.5).validate()


def test_anthropic_config_invalid_top_k():
    """Test Anthropic config with invalid top k."""
    with pytest.raises(ConfigError):
        AnthropicConfig(top_k=-1).validate()


def test_rag_config_invalid_context_length():
    """Test RAG config with invalid context length."""
    with pytest.raises(ConfigError):
        RAGConfig(max_context_length=-1).validate()


def test_rag_config_invalid_similarity():
    """Test RAG config with invalid similarity threshold."""
    with pytest.raises(ConfigError):
        RAGConfig(min_similarity=1.5).validate()


def test_in_context_config_invalid_examples():
    """Test in-context config with invalid max examples."""
    with pytest.raises(ConfigError):
        InContextConfig(max_examples=-1).validate()


def test_in_context_config_invalid_threshold():
    """Test in-context config with invalid similarity threshold."""
    with pytest.raises(ConfigError):
        InContextConfig(similarity_threshold=1.5).validate()


def test_retrieval_config_invalid_context_length():
    """Test retrieval config with invalid context length."""
    with pytest.raises(ConfigError):
        RetrievalConfig(max_context_length=-1).validate()


def test_retrieval_config_invalid_similarity():
    """Test retrieval config with invalid similarity threshold."""
    with pytest.raises(ConfigError):
        RetrievalConfig(min_similarity=1.5).validate()


def test_fine_tuning_config_invalid_epochs():
    """Test fine-tuning config with invalid epochs."""
    with pytest.raises(ConfigError):
        FineTuningConfig(num_epochs=-1).validate()


def test_fine_tuning_config_invalid_learning_rate():
    """Test fine-tuning config with invalid learning rate."""
    with pytest.raises(ConfigError):
        FineTuningConfig(learning_rate=-1).validate()


def test_metrics_config_invalid_buffer_size():
    """Test metrics config with invalid buffer size."""
    with pytest.raises(ConfigError):
        MetricsConfig(buffer_size=-1).validate()


def test_logging_config_invalid_format():
    """Test logging config with invalid format."""
    with pytest.raises(ConfigError):
        LoggingConfig(format="").validate()


def test_data_stores_config_invalid_component():
    """Test data stores config with invalid component."""
    vector_store = VectorStoreConfig(dimension=-1)
    with pytest.raises(ConfigError):
        DataStoresConfig(vector_store=vector_store).validate()


def test_llm_config_invalid_component():
    """Test LLM config with invalid component."""
    openai = OpenAIConfig(temperature=2.5)
    with pytest.raises(ConfigError):
        LLMConfig(openai=openai).validate()


def test_learning_config_invalid_component():
    """Test learning config with invalid component."""
    in_context = InContextConfig(max_examples=-1)
    with pytest.raises(ConfigError):
        LearningConfig(in_context=in_context).validate()


def test_monitoring_config_invalid_component():
    """Test monitoring config with invalid component."""
    metrics = MetricsConfig(buffer_size=-1)
    with pytest.raises(ConfigError):
        MonitoringConfig(metrics=metrics).validate() 