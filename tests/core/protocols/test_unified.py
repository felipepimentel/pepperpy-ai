"""Tests for the unified protocol system."""

import pytest

from pepperpy.core.protocols.unified import (
    BaseProtocol,
    ProtocolError,
    ProtocolMetadata,
    ProtocolMonitor,
    ProtocolProvider,
    ProtocolRegistry,
    ProtocolValidator,
)


def test_protocol_metadata():
    """Test protocol metadata creation and conversion."""
    metadata = ProtocolMetadata(
        name="test",
        version="1.0",
        description="Test protocol",
        capabilities=["test1", "test2"],
        metadata={"type": "test"},
    )

    assert metadata.name == "test"
    assert metadata.version == "1.0"
    assert metadata.description == "Test protocol"
    assert metadata.capabilities == ["test1", "test2"]
    assert metadata.metadata == {"type": "test"}

    # Test dictionary conversion
    metadata_dict = metadata.to_dict()
    assert metadata_dict["name"] == "test"
    assert metadata_dict["version"] == "1.0"
    assert metadata_dict["description"] == "Test protocol"
    assert metadata_dict["capabilities"] == ["test1", "test2"]
    assert metadata_dict["metadata"] == {"type": "test"}


class TestProtocol(BaseProtocol[str]):
    """Test protocol implementation."""

    async def initialize(self) -> None:
        """Initialize the protocol."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def validate(self) -> list[str]:
        """Validate protocol state."""
        return []


class TestProvider(ProtocolProvider[str]):
    """Test protocol provider."""

    def __init__(self, name: str, version: str):
        """Initialize the test provider."""
        self._metadata = ProtocolMetadata(
            name=name,
            version=version,
            description="Test provider",
            capabilities=["test"],
            metadata={},
        )

    @property
    def metadata(self) -> ProtocolMetadata:
        """Get provider metadata."""
        return self._metadata

    async def get_implementation(self) -> str:
        """Get protocol implementation."""
        return "test implementation"


class TestBadProvider(ProtocolProvider[str]):
    """Test provider that fails to provide implementation."""

    @property
    def metadata(self) -> ProtocolMetadata:
        """Get provider metadata."""
        return ProtocolMetadata(
            name="bad",
            version="1.0",
            description="Bad provider",
            capabilities=[],
            metadata={},
        )

    async def get_implementation(self) -> str:
        """Get protocol implementation."""
        raise ProtocolError("Failed to get implementation")


class TestRegistry:
    """Tests for the protocol registry."""

    @pytest.fixture
    def registry(self) -> ProtocolRegistry:
        """Fixture providing a protocol registry."""
        return ProtocolRegistry()

    @pytest.fixture
    def provider(self) -> TestProvider:
        """Fixture providing a test provider."""
        return TestProvider("test", "1.0")

    def test_register_protocol(self, registry):
        """Test protocol registration."""
        registry.register_protocol("test", "1.0", TestProtocol)

        assert "test" in registry._protocols
        assert "1.0" in registry._protocols["test"]
        assert registry._protocols["test"]["1.0"] == TestProtocol

    def test_register_duplicate_protocol(self, registry):
        """Test registering duplicate protocol."""
        registry.register_protocol("test", "1.0", TestProtocol)

        with pytest.raises(ProtocolError) as exc:
            registry.register_protocol("test", "1.0", TestProtocol)
        assert exc.value.code == "PROTO001"

    def test_register_provider(self, registry, provider):
        """Test provider registration."""
        registry.register_provider(provider)

        assert provider.metadata.name in registry._providers
        assert provider.metadata.version in registry._providers[provider.metadata.name]

    def test_register_duplicate_provider(self, registry, provider):
        """Test registering duplicate provider."""
        registry.register_provider(provider)

        with pytest.raises(ProtocolError) as exc:
            registry.register_provider(provider)
        assert exc.value.code == "PROTO002"

    @pytest.mark.asyncio
    async def test_get_implementation(self, registry, provider):
        """Test getting implementation."""
        registry.register_provider(provider)

        impl = await registry.get_implementation("test", "1.0")
        assert impl == "test implementation"

    @pytest.mark.asyncio
    async def test_get_latest_implementation(self, registry):
        """Test getting latest implementation version."""
        registry.register_provider(TestProvider("test", "1.0"))
        registry.register_provider(TestProvider("test", "2.0"))

        impl = await registry.get_implementation("test")
        assert impl == "test implementation"

    @pytest.mark.asyncio
    async def test_get_nonexistent_protocol(self, registry):
        """Test getting non-existent protocol."""
        with pytest.raises(ProtocolError) as exc:
            await registry.get_implementation("nonexistent")
        assert exc.value.code == "PROTO003"

    @pytest.mark.asyncio
    async def test_get_nonexistent_version(self, registry, provider):
        """Test getting non-existent version."""
        registry.register_provider(provider)

        with pytest.raises(ProtocolError) as exc:
            await registry.get_implementation("test", "2.0")
        assert exc.value.code == "PROTO004"

    @pytest.mark.asyncio
    async def test_get_failed_implementation(self, registry):
        """Test getting failed implementation."""
        registry.register_provider(TestBadProvider())

        with pytest.raises(ProtocolError) as exc:
            await registry.get_implementation("bad")
        assert exc.value.code == "PROTO005"


class TestValidator:
    """Tests for the protocol validator."""

    @pytest.fixture
    def validator(self) -> ProtocolValidator:
        """Fixture providing a protocol validator."""
        return ProtocolValidator()

    @pytest.mark.asyncio
    async def test_validate_implementation(self, validator):
        """Test implementation validation."""
        protocol = TestProtocol()
        errors = await validator.validate_implementation(TestProtocol, protocol)
        assert not errors

    @pytest.mark.asyncio
    async def test_validate_invalid_implementation(self, validator):
        """Test validation of invalid implementation."""

        class InvalidProtocol:
            pass

        errors = await validator.validate_implementation(
            TestProtocol, InvalidProtocol()
        )
        assert len(errors) > 0
        assert any("does not implement protocol" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_provider(self, validator):
        """Test provider validation."""
        provider = TestProvider("test", "1.0")
        errors = await validator.validate_provider(provider)
        assert not errors

    @pytest.mark.asyncio
    async def test_validate_bad_provider(self, validator):
        """Test validation of bad provider."""
        provider = TestBadProvider()
        errors = await validator.validate_provider(provider)
        assert len(errors) > 0
        assert any("Provider validation failed" in error for error in errors)


class TestMonitor:
    """Tests for the protocol monitor."""

    @pytest.fixture
    def monitor(self) -> ProtocolMonitor:
        """Fixture providing a protocol monitor."""
        return ProtocolMonitor()

    @pytest.mark.asyncio
    async def test_record_operation(self, monitor):
        """Test recording protocol operation."""
        await monitor.record_operation("test", "operation", success=True, label="value")

    @pytest.mark.asyncio
    async def test_record_error(self, monitor):
        """Test recording protocol error."""
        await monitor.record_error("test", "Test error", label="value")
