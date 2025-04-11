"""Tests for resource validation."""

from typing import Any

from .resource_validator import ResourceLimits, ResourceValidator


def test_memory_validation():
    """Test memory usage validation."""
    validator = ResourceValidator(ResourceLimits(max_memory_mb=100))

    # Test under limit
    validator.validate_memory(50, "test.memory")
    result = validator.get_result()
    assert result.is_valid
    assert len(result.warnings) == 1  # Resource usage summary

    # Test warning threshold (>80%)
    validator.validate_memory(85, "test.memory")
    result = validator.get_result()
    assert result.is_valid
    assert len(result.warnings) == 2  # Including threshold warning

    # Test over limit
    validator.validate_memory(120, "test.memory")
    result = validator.get_result()
    assert not result.is_valid
    assert len(result.errors) == 1


def test_token_validation():
    """Test token counting validation."""
    validator = ResourceValidator(ResourceLimits(max_tokens_per_request=100))

    # Test text only
    text = "x" * 400  # Should be ~100 tokens
    validator.validate_tokens(text, "test.tokens")
    result = validator.get_result()
    assert result.is_valid

    # Test with images
    images = [{"quality": "high"}]  # 85 + 340 = 425 tokens
    validator.validate_tokens("test", "test.tokens", images)
    result = validator.get_result()
    assert not result.is_valid
    assert len(result.errors) == 1


def test_parallel_requests():
    """Test parallel request validation."""
    validator = ResourceValidator(ResourceLimits(max_parallel_requests=3))

    # Test under limit
    validator.validate_parallel_requests(2, "test.parallel")
    result = validator.get_result()
    assert result.is_valid

    # Test over limit
    validator.validate_parallel_requests(2, "test.parallel")
    result = validator.get_result()
    assert not result.is_valid


def test_context_size():
    """Test RAG context size validation."""
    validator = ResourceValidator(ResourceLimits(max_context_size_mb=10))

    # Test under limit
    validator.validate_context_size(5, "test.context")
    result = validator.get_result()
    assert result.is_valid

    # Test over limit
    validator.validate_context_size(15, "test.context")
    result = validator.get_result()
    assert not result.is_valid


def test_batch_operations():
    """Test batch operation validation."""
    validator = ResourceValidator(ResourceLimits(max_batch_size=5))

    # Test under limit
    validator.validate_batch_operation("test_op", 3, "test.batch")
    result = validator.get_result()
    assert result.is_valid

    # Test over limit
    validator.validate_batch_operation("test_op", 7, "test.batch")
    result = validator.get_result()
    assert not result.is_valid


def test_step_resources():
    """Test step resource validation."""
    validator = ResourceValidator(
        ResourceLimits(
            max_tokens_per_request=1000, max_parallel_requests=3, max_context_size_mb=10
        )
    )

    # Test chat step
    chat_step: dict[str, Any] = {
        "type": "chat",
        "messages": [
            {"role": "user", "content": "x" * 4000},  # ~1000 tokens
            {
                "role": "assistant",
                "content": {"image_url": "test.jpg", "quality": "high"},
            },
        ],
    }
    validator.validate_step_resources(chat_step, "test.chat")
    result = validator.get_result()
    assert not result.is_valid  # Should exceed token limit

    # Test RAG step
    validator = ResourceValidator(ResourceLimits(max_context_size_mb=10))
    rag_step = {
        "type": "rag",
        "context_text": "x" * 11_000_000,  # 11MB
        "query": "test query",
    }
    validator.validate_step_resources(rag_step, "test.rag")
    result = validator.get_result()
    assert not result.is_valid

    # Test parallel step
    validator = ResourceValidator(ResourceLimits(max_parallel_requests=2))
    parallel_step = {
        "type": "parallel",
        "operations": [
            {"type": "chat", "messages": []},
            {"type": "rag", "query": "test"},
            {"type": "vision", "prompt": "test"},
        ],
    }
    validator.validate_step_resources(parallel_step, "test.parallel")
    result = validator.get_result()
    assert not result.is_valid


def test_resource_summary():
    """Test resource usage summary."""
    validator = ResourceValidator()

    # Add various resource usage
    validator.validate_memory(100, "test.memory")
    validator.validate_context_size(5, "test.context")
    validator.validate_parallel_requests(2, "test.parallel")
    validator.validate_batch_operation("op1", 3, "test.batch")
    validator.validate_batch_operation("op2", 4, "test.batch")

    result = validator.get_result()
    assert result.is_valid

    # Check summary in warnings
    summary = next(w for w in result.warnings if w.message == "Resource usage summary")
    assert summary.details is not None
    assert summary.details["total_memory_mb"] == 100
    assert summary.details["context_size_mb"] == 5
    assert summary.details["active_requests"] == 2
    assert summary.details["batch_operations"] == {"op1": 3, "op2": 4}
