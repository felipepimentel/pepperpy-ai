"""Tests for configuration module."""

import os
import pytest
from pathlib import Path
from typing import Dict, Any
import yaml

from pepperpy.core.config.config import (
    Config,
    ConfigError,
    load_config,
    save_config,
    get_data_store_config
)

from pepperpy.core.config import (
    BaseConfig,
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
    config = BaseConfig(name="test")
    config.validate()  # Should not raise


def test_base_config_from_dict():
    """Test creating base configuration from dictionary."""
    config_dict = {"config_path": None}
    config = BaseConfig.from_dict(config_dict, name="test")
    assert config.config_path is None


def test_base_config_to_dict():
    """Test converting base configuration to dictionary."""
    config = BaseConfig(name="test")
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "config_path" in config_dict


def test_base_config_save_load(tmp_path):
    """Test saving and loading base configuration."""
    config = BaseConfig(name="test")
    yaml_path = tmp_path / "config.yaml"
    config.save(yaml_path)
    loaded_config = BaseConfig.from_yaml(yaml_path, name="test")
    assert loaded_config.config_path is None


def test_vector_store_config_validation():
    """Test vector store configuration validation."""
    config = VectorStoreConfig(name="test", dimension=512)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        VectorStoreConfig(name="test", dimension=-1).validate()


def test_document_store_config_validation():
    """Test document store configuration validation."""
    config = DocumentStoreConfig(name="test", chunk_size=1000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        DocumentStoreConfig(name="test", chunk_size=-1).validate()


def test_memory_store_config_validation():
    """Test memory store configuration validation."""
    config = MemoryStoreConfig(name="test", short_term_max_size=1000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        MemoryStoreConfig(name="test", short_term_max_size=-1).validate()


def test_openai_config_validation():
    """Test OpenAI configuration validation."""
    config = OpenAIConfig(name="test", temperature=0.7)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        OpenAIConfig(name="test", temperature=2.5).validate()


def test_anthropic_config_validation():
    """Test Anthropic configuration validation."""
    config = AnthropicConfig(name="test", temperature=0.7)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        AnthropicConfig(name="test", temperature=1.5).validate()


def test_rag_config_validation():
    """Test RAG configuration validation."""
    config = RAGConfig(name="test", max_context_length=4000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        RAGConfig(name="test", max_context_length=-1).validate()


def test_in_context_config_validation():
    """Test in-context learning configuration validation."""
    config = InContextConfig(name="test", max_examples=5)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        InContextConfig(name="test", max_examples=-1).validate()


def test_retrieval_config_validation():
    """Test retrieval-based learning configuration validation."""
    config = RetrievalConfig(name="test", max_context_length=2000)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        RetrievalConfig(name="test", max_context_length=-1).validate()


def test_fine_tuning_config_validation():
    """Test fine-tuning configuration validation."""
    config = FineTuningConfig(name="test", num_epochs=3)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        FineTuningConfig(name="test", num_epochs=-1).validate()


def test_metrics_config_validation():
    """Test metrics configuration validation."""
    config = MetricsConfig(name="test", buffer_size=100)
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        MetricsConfig(name="test", buffer_size=-1).validate()


def test_logging_config_validation():
    """Test logging configuration validation."""
    config = LoggingConfig(name="test", level="INFO")
    config.validate()  # Should not raise
    
    with pytest.raises(ConfigError):
        LoggingConfig(name="test", format="").validate()


def test_data_stores_config_validation():
    """Test data stores configuration validation."""
    config = DataStoresConfig(name="test")
    config.validate()  # Should not raise


def test_llm_config_validation():
    """Test LLM configuration validation."""
    config = LLMConfig(name="test")
    config.validate()  # Should not raise


def test_learning_config_validation():
    """Test learning strategies configuration validation."""
    config = LearningConfig(name="test")
    config.validate()  # Should not raise


def test_monitoring_config_validation():
    """Test monitoring configuration validation."""
    config = MonitoringConfig(name="test")
    config.validate()  # Should not raise 