"""Test configuration for validation tests."""

from collections.abc import AsyncGenerator

import pytest

from pepperpy.validation import BaseSchema, SchemaManager


class TestSchema(BaseSchema):
    """Test schema."""

    name: str
    value: int


@pytest.fixture
async def schema_manager() -> AsyncGenerator[SchemaManager, None]:
    """Create schema manager fixture."""
    manager = SchemaManager()
    await manager.initialize()
    yield manager
    manager.clear()
