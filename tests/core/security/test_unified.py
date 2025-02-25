"""Tests for the unified security system."""

from datetime import datetime, timedelta

import pytest

from pepperpy.core.security.unified import (
    BaseSecurityProvider,
    SecurityContext,
    SecurityError,
    SecurityLevel,
    SecurityManager,
    SecurityMonitor,
)


def test_security_level():
    """Test security level enumeration."""
    assert SecurityLevel.LOW.value == "low"
    assert SecurityLevel.MEDIUM.value == "medium"
    assert SecurityLevel.HIGH.value == "high"


def test_security_context():
    """Test security context creation and methods."""
    context = SecurityContext(
        user_id="test_user",
        roles=["admin", "user"],
        permissions=["resource:read", "resource:write"],
        level=SecurityLevel.MEDIUM,
        metadata={"test": "value"},
        expires_at=datetime.now() + timedelta(hours=1),
    )

    assert context.user_id == "test_user"
    assert "admin" in context.roles
    assert "resource:read" in context.permissions
    assert context.level == SecurityLevel.MEDIUM
    assert context.metadata["test"] == "value"
    assert not context.is_expired()

    # Test permission checks
    assert context.has_permission("resource:read")
    assert not context.has_permission("resource:delete")

    # Test role checks
    assert context.has_role("admin")
    assert not context.has_role("superuser")

    # Test dictionary conversion
    context_dict = context.to_dict()
    assert context_dict["user_id"] == "test_user"
    assert "admin" in context_dict["roles"]
    assert "resource:read" in context_dict["permissions"]
    assert context_dict["level"] == "medium"
    assert context_dict["metadata"]["test"] == "value"
    assert isinstance(context_dict["created_at"], str)
    assert isinstance(context_dict["expires_at"], str)


class TestBaseSecurityProvider:
    """Tests for the base security provider."""

    @pytest.fixture
    def provider(self) -> BaseSecurityProvider[str]:
        """Fixture providing a base security provider."""
        return BaseSecurityProvider()

    @pytest.mark.asyncio
    async def test_authenticate(self, provider):
        """Test authentication."""
        credentials = {"username": "test", "password": "test"}
        context = await provider.authenticate(credentials)

        assert context.user_id == "test_user"
        assert "user" in context.roles
        assert "resource:read" in context.permissions
        assert context.level == SecurityLevel.MEDIUM
        assert not context.is_expired()

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, provider):
        """Test authentication failure."""
        credentials = {"username": "invalid"}
        with pytest.raises(SecurityError) as exc:
            await provider.authenticate(credentials)
        assert exc.value.code == "SEC002"

    @pytest.mark.asyncio
    async def test_authorize(self, provider):
        """Test authorization."""
        context = SecurityContext(
            user_id="test_user",
            roles=["user"],
            permissions=["resource:read"],
            level=SecurityLevel.MEDIUM,
            metadata={},
        )

        # Test with direct permission
        assert await provider.authorize(context, "resource", "read")

        # Test without permission
        assert not await provider.authorize(context, "resource", "write")

        # Test with expired context
        context.expires_at = datetime.now() - timedelta(hours=1)
        assert not await provider.authorize(context, "resource", "read")

    @pytest.mark.asyncio
    async def test_validate(self, provider):
        """Test context validation."""
        # Valid context
        context = SecurityContext(
            user_id="test_user",
            roles=["user"],
            permissions=["resource:read"],
            level=SecurityLevel.MEDIUM,
            metadata={},
        )
        errors = await provider.validate(context)
        assert not errors

        # Invalid context
        invalid_context = SecurityContext(
            user_id="",
            roles=[],
            permissions=[],
            level=SecurityLevel.MEDIUM,
            metadata={},
        )
        errors = await provider.validate(invalid_context)
        assert len(errors) == 2
        assert "Missing user ID" in errors
        assert "No roles assigned" in errors

    @pytest.mark.asyncio
    async def test_encryption(self, provider):
        """Test data encryption and decryption."""
        context = SecurityContext(
            user_id="test_user",
            roles=["user"],
            permissions=["resource:read"],
            level=SecurityLevel.MEDIUM,
            metadata={},
        )

        # Test encryption
        data = "test data"
        encrypted = await provider.encrypt(data, context)
        assert isinstance(encrypted, bytes)

        # Test decryption
        decrypted = await provider.decrypt(encrypted, context)
        assert decrypted is None  # Base implementation returns None

        # Test with expired context
        context.expires_at = datetime.now() - timedelta(hours=1)
        with pytest.raises(SecurityError) as exc:
            await provider.encrypt(data, context)
        assert "expired context" in str(exc.value)

        with pytest.raises(SecurityError) as exc:
            await provider.decrypt(encrypted, context)
        assert "expired context" in str(exc.value)


class TestSecurityManager:
    """Tests for the security manager."""

    @pytest.fixture
    def manager(self) -> SecurityManager:
        """Fixture providing a security manager."""
        return SecurityManager()

    @pytest.fixture
    def provider(self) -> BaseSecurityProvider[str]:
        """Fixture providing a security provider."""
        return BaseSecurityProvider()

    def test_register_provider(self, manager, provider):
        """Test provider registration."""
        manager.register_provider("test", provider)
        assert "test" in manager._providers

        # Test default provider
        manager.register_provider("default_test", provider, default=True)
        assert manager._providers["default"] == provider

        # Test duplicate registration
        with pytest.raises(SecurityError) as exc:
            manager.register_provider("test", provider)
        assert exc.value.code == "SEC005"

    @pytest.mark.asyncio
    async def test_authenticate(self, manager, provider):
        """Test authentication through manager."""
        manager.register_provider("test", provider)

        # Test with specific provider
        context = await manager.authenticate(
            {"username": "test"},
            provider="test",
        )
        assert context.user_id == "test_user"

        # Test with non-existent provider
        with pytest.raises(SecurityError) as exc:
            await manager.authenticate({}, provider="nonexistent")
        assert exc.value.code == "SEC006"

    @pytest.mark.asyncio
    async def test_authorize(self, manager, provider):
        """Test authorization through manager."""
        manager.register_provider("test", provider)

        context = SecurityContext(
            user_id="test_user",
            roles=["user"],
            permissions=["resource:read"],
            level=SecurityLevel.MEDIUM,
            metadata={},
        )

        # Test with specific provider
        result = await manager.authorize(
            context,
            "resource",
            "read",
            provider="test",
        )
        assert result

        # Test with non-existent provider
        with pytest.raises(SecurityError) as exc:
            await manager.authorize(
                context,
                "resource",
                "read",
                provider="nonexistent",
            )
        assert exc.value.code == "SEC007"

    @pytest.mark.asyncio
    async def test_encryption(self, manager, provider):
        """Test encryption through manager."""
        manager.register_provider("test", provider)

        context = SecurityContext(
            user_id="test_user",
            roles=["user"],
            permissions=["resource:read"],
            level=SecurityLevel.MEDIUM,
            metadata={},
        )

        # Test encryption
        data = "test data"
        encrypted = await manager.encrypt(data, context, provider="test")
        assert isinstance(encrypted, bytes)

        # Test decryption
        decrypted = await manager.decrypt(encrypted, context, provider="test")
        assert decrypted is None  # Base implementation returns None

        # Test with non-existent provider
        with pytest.raises(SecurityError) as exc:
            await manager.encrypt(data, context, provider="nonexistent")
        assert exc.value.code == "SEC008"

        with pytest.raises(SecurityError) as exc:
            await manager.decrypt(encrypted, context, provider="nonexistent")
        assert exc.value.code == "SEC009"


class TestSecurityMonitor:
    """Tests for the security monitor."""

    @pytest.fixture
    def monitor(self) -> SecurityMonitor:
        """Fixture providing a security monitor."""
        return SecurityMonitor()

    @pytest.mark.asyncio
    async def test_record_event(self, monitor):
        """Test recording security events."""
        context = SecurityContext(
            user_id="test_user",
            roles=["user"],
            permissions=["resource:read"],
            level=SecurityLevel.MEDIUM,
            metadata={},
        )

        # Test successful event
        await monitor.record_event(
            "test_event",
            context=context,
            success=True,
            resource="test_resource",
        )

        # Test failed event
        await monitor.record_event(
            "test_event",
            context=context,
            success=False,
            error="Test error",
        )

        # Test event without context
        await monitor.record_event(
            "test_event",
            success=True,
            resource="test_resource",
        )
