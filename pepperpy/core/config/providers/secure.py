"""Secure configuration provider that encrypts sensitive data."""

import base64
import json
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pepperpy.core.config.providers.base import ConfigProvider
from pepperpy.core.config.types import ConfigValue


class SecureConfigProvider(ConfigProvider):
    """Configuration provider that encrypts sensitive values."""

    def __init__(self, file_path: str, password: str):
        """Initialize the secure config provider.

        Args:
            file_path: Path to the encrypted configuration file
            password: Password used for encryption/decryption
        """
        self.file_path = Path(file_path)
        self._config: Dict[str, ConfigValue] = {}

        # Generate encryption key from password
        salt = b"pepperpy_secure_config"  # Constant salt for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self._fernet = Fernet(key)

        self._ensure_file_exists()
        self.load()

    def _ensure_file_exists(self) -> None:
        """Ensure the configuration file exists."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.save()

    def _encrypt_value(self, value: ConfigValue) -> str:
        """Encrypt a configuration value."""
        serialized = json.dumps(value)
        encrypted = self._fernet.encrypt(serialized.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def _decrypt_value(self, encrypted: str) -> ConfigValue:
        """Decrypt a configuration value."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt value: {e}")

    def get(self, key: str) -> Optional[ConfigValue]:
        """Retrieve a configuration value by key."""
        encrypted = self._config.get(key)
        if encrypted is not None:
            return self._decrypt_value(encrypted)
        return None

    def set(self, key: str, value: ConfigValue) -> None:
        """Set a configuration value."""
        encrypted = self._encrypt_value(value)
        self._config[key] = encrypted
        self.save()

    def delete(self, key: str) -> bool:
        """Delete a configuration value."""
        if key in self._config:
            del self._config[key]
            self.save()
            return True
        return False

    def clear(self) -> None:
        """Clear all configuration values."""
        self._config.clear()
        self.save()

    def load(self) -> Dict[str, ConfigValue]:
        """Load all configuration values from file."""
        try:
            if self.file_path.exists():
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
        except (json.JSONDecodeError, OSError):
            # If file is corrupted or can't be read, start with empty config
            self._config = {}
        return self._config

    def save(self) -> None:
        """Save all configuration values to file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, sort_keys=True)
        except OSError as e:
            raise RuntimeError(f"Failed to save configuration: {e}")

    def exists(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return key in self._config

    def get_namespace(self, namespace: str) -> Dict[str, ConfigValue]:
        """Get all configuration values under a namespace."""
        encrypted_values = {
            k: v for k, v in self._config.items() if k.startswith(f"{namespace}.")
        }
        return {k: self._decrypt_value(v) for k, v in encrypted_values.items()}
