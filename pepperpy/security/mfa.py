"""Multi-factor authentication implementation."""

import base64
import hmac
import secrets
import struct
import time
from typing import List, Optional, Tuple

from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics import MetricsCollector
from pepperpy.security.errors import AuthenticationError, ConfigurationError
from pepperpy.security.types import MFAConfig, MFACredentials, MFAType


class MFAManager(Lifecycle):
    """Multi-factor authentication manager.
    
    Handles:
    - TOTP generation and validation
    - Backup codes management
    - Device registration
    - MFA policy enforcement
    """

    def __init__(
        self,
        config: MFAConfig,
        metrics: Optional[MetricsCollector] = None
    ) -> None:
        """Initialize MFA manager.
        
        Args:
            config: MFA configuration
            metrics: Optional metrics collector
        """
        super().__init__()
        self.config = config
        self._metrics = metrics
        self._secrets: dict[str, bytes] = {}  # user_id -> secret
        self._backup_codes: dict[str, set[str]] = {}  # user_id -> codes
        self._devices: dict[str, list[str]] = {}  # user_id -> device_ids
        
        # Set up metrics
        if metrics:
            self._mfa_attempts = metrics.counter(
                "mfa_attempts",
                description="Number of MFA attempts"
            )
            self._mfa_failures = metrics.counter(
                "mfa_failures",
                description="Number of failed MFA attempts"
            )

    async def _initialize(self) -> None:
        """Initialize the MFA manager."""
        if not self.config.enabled:
            raise ConfigurationError("MFA is not enabled")

    async def _cleanup(self) -> None:
        """Clean up resources."""
        self._secrets.clear()
        self._backup_codes.clear()
        self._devices.clear()

    def generate_secret(self, user_id: str) -> Tuple[bytes, List[str]]:
        """Generate TOTP secret and backup codes.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (secret, backup_codes)
        """
        # Generate secret
        secret = base64.b32encode(secrets.token_bytes(20))
        self._secrets[user_id] = secret
        
        # Generate backup codes
        backup_codes = [
            secrets.token_hex(4)
            for _ in range(self.config.backup_codes_count)
        ]
        self._backup_codes[user_id] = set(backup_codes)
        
        return secret, backup_codes

    def register_device(self, user_id: str, device_id: str) -> None:
        """Register MFA device.
        
        Args:
            user_id: User identifier
            device_id: Device identifier
        """
        if user_id not in self._devices:
            self._devices[user_id] = []
        self._devices[user_id].append(device_id)

    def verify_code(
        self,
        user_id: str,
        credentials: MFACredentials
    ) -> bool:
        """Verify MFA code.
        
        Args:
            user_id: User identifier
            credentials: MFA credentials
            
        Returns:
            True if code is valid
            
        Raises:
            AuthenticationError: If verification fails
        """
        if self._metrics:
            self._mfa_attempts.inc()
            
        try:
            if credentials.type == MFAType.TOTP:
                return self._verify_totp(user_id, credentials.code)
            elif credentials.type in (MFAType.SMS, MFAType.EMAIL):
                return self._verify_otp(user_id, credentials.code)
            else:
                raise AuthenticationError(f"Unsupported MFA type: {credentials.type}")
                
        except Exception as e:
            if self._metrics:
                self._mfa_failures.inc()
            raise AuthenticationError(f"MFA verification failed: {e}")

    def _verify_totp(self, user_id: str, code: str) -> bool:
        """Verify TOTP code.
        
        Args:
            user_id: User identifier
            code: TOTP code
            
        Returns:
            True if code is valid
        """
        if user_id not in self._secrets:
            raise AuthenticationError("No TOTP secret found")
            
        secret = self._secrets[user_id]
        
        # Check backup codes first
        if user_id in self._backup_codes and code in self._backup_codes[user_id]:
            self._backup_codes[user_id].remove(code)
            return True
            
        # Verify TOTP
        try:
            code_int = int(code)
        except ValueError:
            return False
            
        # Get current timestamp
        timestamp = int(time.time() // 30)
        
        # Check current and previous intervals
        for delta in (0, -1, 1):
            if self._generate_totp(secret, timestamp + delta) == code_int:
                return True
                
        return False

    def _verify_otp(self, user_id: str, code: str) -> bool:
        """Verify one-time password.
        
        Args:
            user_id: User identifier
            code: One-time password
            
        Returns:
            True if code is valid
        """
        # This is a placeholder for SMS/Email OTP verification
        # In a real implementation, this would verify against stored OTPs
        return False

    def _generate_totp(self, secret: bytes, timestamp: int) -> int:
        """Generate TOTP code.
        
        Args:
            secret: TOTP secret
            timestamp: Current timestamp
            
        Returns:
            Generated TOTP code
        """
        # Generate HMAC-SHA1
        msg = struct.pack(">Q", timestamp)
        h = hmac.new(secret, msg, "sha1").digest()
        
        # Get offset
        offset = h[-1] & 0xf
        
        # Generate 4-byte code
        code = struct.unpack(">I", h[offset:offset + 4])[0]
        
        # Return 6-digit code
        return code & 0x7fffffff % 1000000 