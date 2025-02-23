"""Security tests.

This module provides tests for the security components.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from pepperpy.core.errors import NotFoundError, ValidationError
from pepperpy.security import (
    AuthenticationError,
    AuthorizationError,
    BaseSecurityProvider,
    Credentials,
    Permission,
    Policy,
    ProtectionPolicy,
    Role,
    SecurityConfig,
    SecurityContext,
    SecurityScope,
    Token,
)


@pytest.fixture
async def security_provider():
    """Create security provider for testing."""
    provider = BaseSecurityProvider()
    await provider.initialize()
    try:
        yield provider
    finally:
        await provider.shutdown()


@pytest.fixture
def test_credentials():
    """Create test credentials."""
    return Credentials(
        user_id="test_user",
        password="test_password",
        scopes={SecurityScope.READ},
    )


@pytest.fixture
def test_token():
    """Create test token."""
    return Token(
        token_id=uuid4(),
        user_id="test_user",
        scopes={SecurityScope.READ},
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )


@pytest.fixture
def test_role():
    """Create test role."""
    return Role(
        name="test_role",
        permissions={Permission.READ},
        description="Test role",
    )


@pytest.fixture
def test_policy():
    """Create test policy."""
    return Policy(
        name="test_policy",
        roles={"test_role"},
        scopes={SecurityScope.READ},
        resources={"test_resource"},
        actions={Permission.READ},
    )


@pytest.fixture
def test_protection_policy():
    """Create test protection policy."""
    return ProtectionPolicy(
        name="test_policy",
        field_name="test_field",
        protection_type="encryption",
        required_scopes={SecurityScope.READ},
    )


@pytest.mark.asyncio
async def test_authentication(security_provider, test_credentials):
    """Test authentication functionality."""
    # Test authentication
    token = await security_provider.authenticate(test_credentials)
    assert token is not None
    assert token.user_id == test_credentials.user_id
    assert token.scopes == test_credentials.scopes

    # Test token validation
    assert await security_provider.validate_token(token)

    # Test token revocation
    await security_provider.revoke_token(token)
    assert not await security_provider.validate_token(token)

    # Test invalid credentials
    with pytest.raises(AuthenticationError):
        await security_provider.authenticate(
            Credentials(
                user_id="invalid",
                password="invalid",
            )
        )


@pytest.mark.asyncio
async def test_authorization(security_provider, test_credentials, test_role):
    """Test authorization functionality."""
    # Create role
    role = await security_provider.create_role(test_role)
    assert role.name == test_role.name
    assert role.permissions == test_role.permissions

    # Authenticate user
    token = await security_provider.authenticate(test_credentials)
    context = await security_provider.get_security_context(token)

    # Test permission check
    assert await security_provider.has_permission(
        context,
        Permission.READ,
        "test_resource",
    )

    # Test scope check
    assert await security_provider.has_scope(context, SecurityScope.READ)

    # Test role check
    assert await security_provider.has_role(context, test_role.name)

    # Test invalid permission
    assert not await security_provider.has_permission(
        context,
        Permission.WRITE,
        "test_resource",
    )


@pytest.mark.asyncio
async def test_data_protection(security_provider, test_protection_policy):
    """Test data protection functionality."""
    # Create protection policy
    policy = await security_provider.create_protection_policy(test_protection_policy)
    assert policy.name == test_protection_policy.name

    # Test encryption
    data = "sensitive data"
    encrypted = await security_provider.encrypt(data, policy.name)
    assert encrypted != data.encode()

    # Test decryption
    decrypted = await security_provider.decrypt(encrypted, policy.name)
    assert decrypted.decode() == data

    # Test policy update
    policy.description = "Updated policy"
    updated = await security_provider.update_protection_policy(policy)
    assert updated.description == "Updated policy"

    # Test policy deletion
    await security_provider.delete_protection_policy(policy.name)
    with pytest.raises(NotFoundError):
        await security_provider.get_protection_policies()


@pytest.mark.asyncio
async def test_password_hashing(security_provider):
    """Test password hashing functionality."""
    # Test password hashing
    password = "test_password"
    hashed = await security_provider.hash_password(password)
    assert hashed != password

    # Test password verification
    assert await security_provider.verify_password(password, hashed)
    assert not await security_provider.verify_password("wrong_password", hashed)


@pytest.mark.asyncio
async def test_security_config(security_provider):
    """Test security configuration."""
    # Get default config
    config = await security_provider.get_config()
    assert isinstance(config, SecurityConfig)
    assert config.min_password_length == 8

    # Update config
    config.min_password_length = 12
    updated = await security_provider.update_config(config)
    assert updated.min_password_length == 12

    # Test invalid config
    with pytest.raises(ValidationError):
        config.min_password_length = -1
        await security_provider.update_config(config)


@pytest.mark.asyncio
async def test_error_handling(security_provider, test_token):
    """Test error handling."""
    # Test authentication error
    with pytest.raises(AuthenticationError):
        await security_provider.authenticate(
            Credentials(
                user_id="invalid",
                password="invalid",
            )
        )

    # Test authorization error
    with pytest.raises(AuthorizationError):
        context = SecurityContext(
            user_id="test_user",
            current_token=test_token,
            roles=set(),
            active_scopes=set(),
        )
        await security_provider.has_permission(
            context,
            Permission.ADMIN,
            "test_resource",
        )

    # Test validation error
    with pytest.raises(ValidationError):
        await security_provider.create_role(
            Role(
                name="",  # Invalid name
                permissions={Permission.READ},
            )
        )

    # Test not found error
    with pytest.raises(NotFoundError):
        await security_provider.delete_role("non_existent_role")
