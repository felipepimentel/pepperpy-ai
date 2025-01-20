"""Tests for configuration module."""

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


def test_base_config_validation():
    """Test base configuration validation."""
    config = BaseConfig()
    config.validate()  # Should not raise


def test_base_config_from_dict():
    """Test creating base configuration from dictionary."""
    config_dict = {"config_path": None}
    config = BaseConfig.from_dict(config_dict)
    assert config.config_path is None


def test_base_config_to_dict():
    """Test converting base configuration to dictionary."""
    config = BaseConfig()
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "config_path" in config_dict


def test_base_config_save_load(tmp_path):
    """Test saving and loading base configuration."""
    config = BaseConfig()
    yaml_path = tmp_path / "config.yaml"
    config.save(yaml_path)
    loaded_config = BaseConfig.from_yaml(yaml_path)
    assert loaded_config.config_path is None


def test_vector_store_config_validation():
    """Test vector store configuration validation."""
    config = VectorStoreConfig(dimension=512)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        VectorStoreConfig(dimension=-1).validate()


def test_document_store_config_validation():
    """Test document store configuration validation."""
    config = DocumentStoreConfig(chunk_size=1000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        DocumentStoreConfig(chunk_size=-1).validate()


def test_memory_store_config_validation():
    """Test memory store configuration validation."""
    config = MemoryStoreConfig(short_term_max_size=1000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        MemoryStoreConfig(short_term_max_size=-1).validate()


def test_openai_config_validation():
    """Test OpenAI configuration validation."""
    config = OpenAIConfig(temperature=0.7)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        OpenAIConfig(temperature=2.5).validate()


def test_anthropic_config_validation():
    """Test Anthropic configuration validation."""
    config = AnthropicConfig(temperature=0.7)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        AnthropicConfig(temperature=1.5).validate()


def test_rag_config_validation():
    """Test RAG configuration validation."""
    config = RAGConfig(max_context_length=4000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        RAGConfig(max_context_length=-1).validate()


def test_in_context_config_validation():
    """Test in-context learning configuration validation."""
    config = InContextConfig(max_examples=5)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        InContextConfig(max_examples=-1).validate()


def test_retrieval_config_validation():
    """Test retrieval-based learning configuration validation."""
    config = RetrievalConfig(max_context_length=2000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        RetrievalConfig(max_context_length=-1).validate()


def test_fine_tuning_config_validation():
    """Test fine-tuning configuration validation."""
    config = FineTuningConfig(num_epochs=3)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        FineTuningConfig(num_epochs=-1).validate()


def test_metrics_config_validation():
    """Test metrics configuration validation."""
    config = MetricsConfig(buffer_size=100)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        MetricsConfig(buffer_size=-1).validate()


def test_logging_config_validation():
    """Test logging configuration validation."""
    config = LoggingConfig(level="INFO")
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        LoggingConfig(format="").validate()


def test_data_stores_config_validation():
    """Test data stores configuration validation."""
    config = DataStoresConfig()
    config.validate()  # Should not raise


def test_llm_config_validation():
    """Test LLM configuration validation."""
    config = LLMConfig()
    config.validate()  # Should not raise


def test_learning_config_validation():
    """Test learning strategies configuration validation."""
    config = LearningConfig()
    config.validate()  # Should not raise


def test_monitoring_config_validation():
    """Test monitoring configuration validation."""
    config = MonitoringConfig()
    config.validate()  # Should not raise 