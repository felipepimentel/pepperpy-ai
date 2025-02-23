"""Tests for validation system."""

from datetime import datetime

import pytest

from pepperpy.core.errors import ValidationError
from pepperpy.validation import SchemaManager
from tests.validation.conftest import TestSchema


def test_base_schema() -> None:
    """Test base schema functionality."""
    # Test creation
    schema = TestSchema(name="test", value=42, version="1.0.0")
    assert schema.name == "test"
    assert schema.value == 42
    assert schema.version == "1.0.0"
    assert isinstance(schema.created_at, datetime)
    assert isinstance(schema.updated_at, datetime)

    # Test immutability
    with pytest.raises(Exception):
        schema.name = "changed"  # type: ignore

    # Test timestamp update
    old_updated = schema.updated_at
    data = schema.dict()
    assert data["updated_at"] > old_updated

    # Test JSON schema
    json_schema = TestSchema.get_json_schema()
    assert json_schema["properties"]["name"]["type"] == "string"
    assert json_schema["properties"]["value"]["type"] == "integer"


def test_schema_registration(schema_manager: SchemaManager) -> None:
    """Test schema registration."""
    # Test registration
    schema_manager.register_schema("test", TestSchema)
    assert "test" in schema_manager.get_schema_names()

    # Test duplicate registration
    with pytest.raises(ValidationError):
        schema_manager.register_schema("test", TestSchema)

    # Test invalid schema
    class InvalidSchema:
        pass

    with pytest.raises(ValidationError):
        schema_manager.register_schema("invalid", InvalidSchema)  # type: ignore


@pytest.mark.asyncio
async def test_schema_validation(schema_manager: SchemaManager) -> None:
    """Test schema validation."""
    schema_manager.register_schema("test", TestSchema)

    # Test valid data
    data = {
        "name": "test",
        "value": 42,
        "version": "1.0.0",
    }
    instance = await schema_manager.validate("test", data)
    assert isinstance(instance, TestSchema)
    assert instance.name == "test"
    assert instance.value == 42

    # Test invalid data
    invalid_data = {
        "name": "test",
        "value": "not an integer",
        "version": "1.0.0",
    }
    with pytest.raises(ValidationError):
        await schema_manager.validate("test", invalid_data)

    # Test missing schema
    with pytest.raises(ValidationError):
        await schema_manager.validate("missing", data)

    # Test version handling
    data_no_version = {
        "name": "test",
        "value": 42,
    }
    instance = await schema_manager.validate("test", data_no_version, version="2.0.0")
    assert instance.version == "2.0.0"


def test_schema_retrieval(schema_manager: SchemaManager) -> None:
    """Test schema retrieval."""
    schema_manager.register_schema("test", TestSchema)

    # Test get schema
    schema = schema_manager.get_schema("test")
    assert schema is TestSchema

    # Test get missing schema
    assert schema_manager.get_schema("missing") is None

    # Test get schema names
    assert "test" in schema_manager.get_schema_names()

    # Test get JSON schema
    json_schema = schema_manager.get_json_schema("test")
    assert json_schema is not None
    assert json_schema["properties"]["name"]["type"] == "string"
    assert json_schema["properties"]["value"]["type"] == "integer"

    # Test get missing JSON schema
    assert schema_manager.get_json_schema("missing") is None


def test_schema_clear(schema_manager: SchemaManager) -> None:
    """Test schema clearing."""
    schema_manager.register_schema("test", TestSchema)
    assert "test" in schema_manager.get_schema_names()

    schema_manager.clear()
    assert not schema_manager.get_schema_names()


@pytest.mark.asyncio
async def test_schema_metrics(schema_manager: SchemaManager) -> None:
    """Test schema validation metrics."""
    schema_manager.register_schema("test", TestSchema)

    # Test successful validation metrics
    data = {
        "name": "test",
        "value": 42,
        "version": "1.0.0",
    }
    await schema_manager.validate("test", data)

    # Test error validation metrics
    invalid_data = {
        "name": "test",
        "value": "not an integer",
        "version": "1.0.0",
    }
    with pytest.raises(ValidationError):
        await schema_manager.validate("test", invalid_data)
