"""Protected document handling for document processing.

This module provides functionality for handling password-protected documents
in the document processing pipeline.
"""

import base64
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)

# Try to import document handling libraries
try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import io

    import msoffcrypto

    MSOFFCRYPTO_AVAILABLE = True
except ImportError:
    MSOFFCRYPTO_AVAILABLE = False

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class ProtectedDocumentError(PepperpyError):
    """Error raised during protected document operations."""

    pass


class PasswordStore:
    """Storage for document passwords.

    This class provides a secure storage for document passwords, allowing
    automatic decryption of documents without requiring passwords every time.
    """

    def __init__(
        self,
        store_type: str = "memory",
        store_path: Optional[Union[str, Path]] = None,
        encryption_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize password store.

        Args:
            store_type: Type of storage ('memory', 'file', or 'keyring')
            store_path: Path to password store file (for 'file' store)
            encryption_key: Key for encrypting stored passwords
            **kwargs: Additional configuration options
        """
        self.store_type = store_type
        self.config = kwargs
        self.passwords: Dict[str, str] = {}

        # Set up store based on type
        if store_type == "memory":
            # Use in-memory storage (lost when process terminates)
            pass
        elif store_type == "file":
            # File-based storage
            if not store_path:
                raise ProtectedDocumentError("File store requires a store_path")

            if isinstance(store_path, str):
                store_path = Path(store_path)

            self.store_path = store_path

            # Check if encryption is available
            if not CRYPTOGRAPHY_AVAILABLE:
                logger.warning(
                    "Cryptography library not available. Passwords will be stored with minimal protection."
                )

            # Create directory if it doesn't exist
            self.store_path.parent.mkdir(parents=True, exist_ok=True)

            # Set encryption key
            self.encryption_key = encryption_key or os.environ.get(
                "PEPPERPY_PASSWORD_STORE_KEY"
            )
            if not self.encryption_key:
                logger.warning(
                    "No encryption key provided for password store. "
                    "Using default key, which is less secure."
                )
                self.encryption_key = "pepperpy_default_key"

            # Load existing passwords
            self._load_passwords()
        elif store_type == "keyring":
            # System keyring-based storage
            try:
                import keyring

                self.keyring = keyring
            except ImportError:
                raise ProtectedDocumentError(
                    "Keyring store requires the keyring package. "
                    "Install with: pip install keyring"
                )
        else:
            raise ProtectedDocumentError(
                f"Unsupported password store type: {store_type}"
            )

    def _load_passwords(self) -> None:
        """Load passwords from file store."""
        if self.store_type != "file" or not hasattr(self, "store_path"):
            return

        if not self.store_path.exists():
            return

        try:
            # Read encrypted passwords
            with open(self.store_path, "rb") as f:
                encrypted_data = f.read()

            # Decrypt data
            if CRYPTOGRAPHY_AVAILABLE:
                from cryptography.fernet import Fernet

                # Derive key from encryption key
                if self.encryption_key:
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=b"pepperpy_password_store",
                        iterations=100000,
                    )
                    key = base64.urlsafe_b64encode(
                        kdf.derive(self.encryption_key.encode())
                    )
                    fernet = Fernet(key)

                    try:
                        decrypted_data = fernet.decrypt(encrypted_data)
                        data = json.loads(decrypted_data.decode())
                        self.passwords = data
                    except Exception as e:
                        logger.warning(f"Error decrypting password store: {e}")
            else:
                # Simple encoding if cryptography is not available
                try:
                    decoded = base64.b64decode(encrypted_data)
                    data = json.loads(decoded.decode())
                    self.passwords = data
                except Exception as e:
                    logger.warning(f"Error decoding password store: {e}")
        except Exception as e:
            logger.warning(f"Error loading password store: {e}")

    def _save_passwords(self) -> None:
        """Save passwords to file store."""
        if self.store_type != "file" or not hasattr(self, "store_path"):
            return

        try:
            # Encrypt and save passwords
            if CRYPTOGRAPHY_AVAILABLE:
                from cryptography.fernet import Fernet

                # Derive key from encryption key
                if self.encryption_key:
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=b"pepperpy_password_store",
                        iterations=100000,
                    )
                    key = base64.urlsafe_b64encode(
                        kdf.derive(self.encryption_key.encode())
                    )
                    fernet = Fernet(key)

                    # Encrypt data
                    data = json.dumps(self.passwords).encode()
                    encrypted_data = fernet.encrypt(data)

                    # Save encrypted data
                    with open(self.store_path, "wb") as f:
                        f.write(encrypted_data)
                else:
                    logger.warning(
                        "Cannot encrypt password store: encryption key is not set"
                    )
                    # Fall back to simple encoding
                    data = json.dumps(self.passwords).encode()
                    encoded = base64.b64encode(data)

                    with open(self.store_path, "wb") as f:
                        f.write(encoded)
            else:
                # Simple encoding if cryptography is not available
                data = json.dumps(self.passwords).encode()
                encoded = base64.b64encode(data)

                with open(self.store_path, "wb") as f:
                    f.write(encoded)
        except Exception as e:
            logger.warning(f"Error saving password store: {e}")

    def _get_document_key(self, document_path: Union[str, Path]) -> str:
        """Generate a key for a document.

        Args:
            document_path: Path to document

        Returns:
            Document key for password lookup
        """
        # Convert to Path object
        if isinstance(document_path, str):
            document_path = Path(document_path)

        # Use absolute path as key
        return str(document_path.absolute())

    def get_password(self, document_path: Union[str, Path]) -> Optional[str]:
        """Get password for a document.

        Args:
            document_path: Path to document

        Returns:
            Document password or None if not found
        """
        document_key = self._get_document_key(document_path)

        if self.store_type == "memory" or self.store_type == "file":
            return self.passwords.get(document_key)
        elif self.store_type == "keyring":
            return self.keyring.get_password("pepperpy", document_key)

        return None

    def set_password(self, document_path: Union[str, Path], password: str) -> None:
        """Set password for a document.

        Args:
            document_path: Path to document
            password: Document password
        """
        document_key = self._get_document_key(document_path)

        if self.store_type == "memory" or self.store_type == "file":
            self.passwords[document_key] = password
            if self.store_type == "file":
                self._save_passwords()
        elif self.store_type == "keyring":
            self.keyring.set_password("pepperpy", document_key, password)

    def clear_password(self, document_path: Union[str, Path]) -> bool:
        """Clear password for a document.

        Args:
            document_path: Path to document

        Returns:
            True if password was cleared, False if not found
        """
        document_key = self._get_document_key(document_path)

        if self.store_type == "memory" or self.store_type == "file":
            if document_key in self.passwords:
                del self.passwords[document_key]
                if self.store_type == "file":
                    self._save_passwords()
                return True
            return False
        elif self.store_type == "keyring":
            try:
                self.keyring.delete_password("pepperpy", document_key)
                return True
            except Exception:
                return False

        return False

    def clear_all(self) -> int:
        """Clear all stored passwords.

        Returns:
            Number of passwords cleared
        """
        if self.store_type == "memory" or self.store_type == "file":
            count = len(self.passwords)
            self.passwords = {}
            if self.store_type == "file":
                self._save_passwords()
            return count
        elif self.store_type == "keyring":
            # Keyring doesn't have a way to clear all passwords for a service
            # This is intentional for security reasons
            logger.warning("Clearing all passwords not supported for keyring store")
            return 0

        return 0


class ProtectedDocumentHandler:
    """Handler for password-protected documents.

    This class provides functionality for detecting and processing
    password-protected documents.
    """

    def __init__(
        self,
        password_store: Optional[PasswordStore] = None,
        temp_dir: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize protected document handler.

        Args:
            password_store: Password store to use
            temp_dir: Temporary directory for decrypted files
            **kwargs: Additional configuration options
        """
        # Set password store
        self.password_store = password_store or PasswordStore()

        # Set temporary directory
        if temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "pepperpy" / "protected"
        elif isinstance(temp_dir, str):
            self.temp_dir = Path(temp_dir)
        else:
            self.temp_dir = temp_dir

        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Set configuration
        self.config = kwargs

    def is_protected(self, file_path: Union[str, Path]) -> bool:
        """Check if a document is password-protected.

        Args:
            file_path: Path to document

        Returns:
            True if document is protected, False otherwise
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            raise ProtectedDocumentError(f"File not found: {file_path}")

        # Get file extension
        extension = file_path.suffix.lower()

        try:
            # Check PDF files
            if extension == ".pdf" and PYMUPDF_AVAILABLE:
                return self._is_pdf_protected(file_path)
            # Check Office files
            elif extension in (".docx", ".xlsx", ".pptx") and MSOFFCRYPTO_AVAILABLE:
                return self._is_office_protected(file_path)
            # Unknown file type or missing dependencies
            else:
                return False
        except Exception as e:
            logger.warning(f"Error checking if file is protected: {e}")
            return False

    def _is_pdf_protected(self, file_path: Path) -> bool:
        """Check if a PDF is password-protected."""
        try:
            # Open PDF and check if it's encrypted
            doc = fitz.open(file_path)
            is_protected = doc.is_encrypted
            doc.close()
            return is_protected
        except Exception as e:
            logger.warning(f"Error checking if PDF is protected: {e}")
            return False

    def _is_office_protected(self, file_path: Path) -> bool:
        """Check if an Office document is password-protected."""
        try:
            # Open file and check if it's encrypted
            with open(file_path, "rb") as f:
                office_file = msoffcrypto.OfficeFile(f)
                return office_file.is_encrypted()
        except Exception as e:
            logger.warning(f"Error checking if Office file is protected: {e}")
            return False

    def decrypt_document(
        self,
        file_path: Union[str, Path],
        password: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Decrypt a password-protected document.

        Args:
            file_path: Path to protected document
            password: Document password (if None, tries to get from store)
            output_path: Path to save decrypted document (if None, uses temp dir)

        Returns:
            Path to decrypted document

        Raises:
            ProtectedDocumentError: If decryption fails
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            raise ProtectedDocumentError(f"File not found: {file_path}")

        # Check if file is protected
        if not self.is_protected(file_path):
            return file_path  # File is not protected, return as is

        # Get password if not provided
        if password is None:
            password = self.password_store.get_password(file_path)
            if password is None:
                raise ProtectedDocumentError(
                    f"No password provided for protected document: {file_path}"
                )

        # Set output path if not provided
        if output_path is None:
            output_path = (
                self.temp_dir / f"{file_path.stem}_decrypted{file_path.suffix}"
            )
        elif isinstance(output_path, str):
            output_path = Path(output_path)

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get file extension
        extension = file_path.suffix.lower()

        # Decrypt based on file type
        try:
            if extension == ".pdf" and PYMUPDF_AVAILABLE:
                self._decrypt_pdf(file_path, password, output_path)
            elif extension in (".docx", ".xlsx", ".pptx") and MSOFFCRYPTO_AVAILABLE:
                self._decrypt_office(file_path, password, output_path)
            else:
                raise ProtectedDocumentError(
                    f"Unsupported file type or missing dependencies: {file_path}"
                )
        except Exception as e:
            raise ProtectedDocumentError(f"Error decrypting document: {e}")

        # Store password for future use
        self.password_store.set_password(file_path, password)

        return output_path

    def _decrypt_pdf(self, file_path: Path, password: str, output_path: Path) -> None:
        """Decrypt a password-protected PDF."""
        try:
            # Open PDF with password
            doc = fitz.open(file_path)

            # Check if password is needed and correct
            if doc.is_encrypted:
                result = doc.authenticate(password)
                if result == 0:
                    raise ProtectedDocumentError("Incorrect password for PDF")

            # Save decrypted PDF
            doc.save(output_path)
            doc.close()
        except Exception as e:
            raise ProtectedDocumentError(f"Error decrypting PDF: {e}")

    def _decrypt_office(
        self, file_path: Path, password: str, output_path: Path
    ) -> None:
        """Decrypt a password-protected Office document."""
        try:
            # Open encrypted file
            with open(file_path, "rb") as f:
                office_file = msoffcrypto.OfficeFile(f)

                # Check if file is encrypted
                if not office_file.is_encrypted():
                    # Just copy the file if it's not encrypted
                    with open(output_path, "wb") as out:
                        f.seek(0)
                        out.write(f.read())
                    return

                # Set password
                try:
                    office_file.load_key(password=password)
                except Exception:
                    raise ProtectedDocumentError(
                        "Incorrect password for Office document"
                    )

                # Save decrypted file
                with open(output_path, "wb") as out:
                    office_file.decrypt(out)
        except Exception as e:
            raise ProtectedDocumentError(f"Error decrypting Office document: {e}")

    def clean_temp_files(self) -> int:
        """Clean up temporary files.

        Returns:
            Number of files deleted
        """
        count = 0
        for path in self.temp_dir.glob("**/*"):
            if path.is_file():
                try:
                    path.unlink()
                    count += 1
                except OSError:
                    # Ignore errors
                    pass

        # Remove empty directories
        for path in sorted(
            self.temp_dir.glob("**/*"), key=lambda p: str(p), reverse=True
        ):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    # Directory not empty or other error
                    pass

        return count


# Global protected document handler instance
_protected_document_handler: Optional[ProtectedDocumentHandler] = None


def get_protected_document_handler(
    password_store: Optional[PasswordStore] = None,
    temp_dir: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> ProtectedDocumentHandler:
    """Get protected document handler instance.

    Args:
        password_store: Password store to use
        temp_dir: Temporary directory for decrypted files
        **kwargs: Additional configuration options

    Returns:
        Protected document handler instance
    """
    global _protected_document_handler

    if _protected_document_handler is None:
        _protected_document_handler = ProtectedDocumentHandler(
            password_store=password_store, temp_dir=temp_dir, **kwargs
        )

    return _protected_document_handler
