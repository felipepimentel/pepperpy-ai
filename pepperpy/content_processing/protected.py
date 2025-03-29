"""Protected content handling module.

This module provides functionality for handling password-protected content files.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.base import PepperpyError
from pepperpy.content_processing.errors import ContentProcessingError

logger = logging.getLogger(__name__)


class ProtectedContentError(PepperpyError):
    """Error raised when handling protected content."""

    pass


class ProtectedContentHandler:
    """Handler for password-protected content files."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize protected content handler.

        Args:
            **kwargs: Additional configuration options
        """
        self._config = kwargs

    async def check_protection(
        self,
        content_path: Union[str, Path],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Check if content is password-protected.

        Args:
            content_path: Path to content file
            **kwargs: Additional options

        Returns:
            Dictionary with protection status and details

        Raises:
            ProtectedContentError: If check fails
        """
        if isinstance(content_path, str):
            content_path = Path(content_path)

        if not content_path.exists():
            raise ProtectedContentError(f"Content not found: {content_path}")

        try:
            # Get file extension
            extension = content_path.suffix.lower()

            # Check protection based on file type
            if extension == ".pdf":
                return await self._check_pdf_protection(content_path, **kwargs)
            elif extension in (".docx", ".xlsx", ".pptx"):
                return await self._check_office_protection(content_path, **kwargs)
            elif extension in (".zip", ".rar", ".7z"):
                return await self._check_archive_protection(content_path, **kwargs)
            else:
                return {
                    "is_protected": False,
                    "protection_type": None,
                    "details": {},
                }

        except Exception as e:
            raise ProtectedContentError(f"Error checking protection: {e}")

    async def unlock_content(
        self,
        content_path: Union[str, Path],
        password: str,
        output_path: Optional[Union[str, Path]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Unlock password-protected content.

        Args:
            content_path: Path to protected content file
            password: Password to unlock content
            output_path: Path to save unlocked content (optional)
            **kwargs: Additional options

        Returns:
            Dictionary with unlocking results

        Raises:
            ProtectedContentError: If unlocking fails
        """
        if isinstance(content_path, str):
            content_path = Path(content_path)

        if not content_path.exists():
            raise ProtectedContentError(f"Content not found: {content_path}")

        try:
            # Set output path if not provided
            if output_path is None:
                output_path = content_path.parent / f"unlocked_{content_path.name}"
            elif isinstance(output_path, str):
                output_path = Path(output_path)

            # Get file extension
            extension = content_path.suffix.lower()

            # Unlock based on file type
            if extension == ".pdf":
                return await self._unlock_pdf(
                    content_path, password, output_path, **kwargs
                )
            elif extension in (".docx", ".xlsx", ".pptx"):
                return await self._unlock_office(
                    content_path, password, output_path, **kwargs
                )
            elif extension in (".zip", ".rar", ".7z"):
                return await self._unlock_archive(
                    content_path, password, output_path, **kwargs
                )
            else:
                raise ProtectedContentError(
                    f"Unsupported file type for unlocking: {extension}"
                )

        except Exception as e:
            raise ProtectedContentError(f"Error unlocking content: {e}")

    async def _check_pdf_protection(
        self,
        content_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Check if PDF is password-protected.

        Args:
            content_path: Path to PDF file
            **kwargs: Additional options

        Returns:
            Dictionary with protection status and details
        """
        try:
            import fitz

            # Open PDF
            doc = fitz.open(content_path)

            # Check protection
            is_protected = doc.needs_pass
            encryption_method = doc.encryption_method if is_protected else None
            permissions = doc.permissions if is_protected else None

            # Close PDF
            doc.close()

            return {
                "is_protected": is_protected,
                "protection_type": "password" if is_protected else None,
                "details": {
                    "encryption_method": encryption_method,
                    "permissions": permissions,
                },
            }

        except ImportError:
            logger.warning("PyMuPDF not installed, using basic PDF check")
            return {
                "is_protected": None,  # Unknown
                "protection_type": None,
                "details": {},
            }
        except Exception as e:
            raise ProtectedContentError(f"Error checking PDF protection: {e}")

    async def _check_office_protection(
        self,
        content_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Check if Office document is password-protected.

        Args:
            content_path: Path to Office document
            **kwargs: Additional options

        Returns:
            Dictionary with protection status and details
        """
        try:
            from msoffcrypto import OfficeFile

            # Open Office document
            with open(content_path, "rb") as f:
                office_file = OfficeFile(f)

                # Check protection
                is_protected = office_file.is_encrypted()

                return {
                    "is_protected": is_protected,
                    "protection_type": "password" if is_protected else None,
                    "details": {},
                }

        except ImportError:
            logger.warning("msoffcrypto-tool not installed, using basic check")
            return {
                "is_protected": None,  # Unknown
                "protection_type": None,
                "details": {},
            }
        except Exception as e:
            raise ProtectedContentError(
                f"Error checking Office document protection: {e}"
            )

    async def _check_archive_protection(
        self,
        content_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Check if archive is password-protected.

        Args:
            content_path: Path to archive file
            **kwargs: Additional options

        Returns:
            Dictionary with protection status and details
        """
        try:
            import py7zr
            import rarfile
            import zipfile

            # Get file extension
            extension = content_path.suffix.lower()

            if extension == ".zip":
                # Check ZIP protection
                with zipfile.ZipFile(content_path) as zip_file:
                    is_protected = any(
                        info.flag_bits & 0x1 for info in zip_file.filelist
                    )
            elif extension == ".rar":
                # Check RAR protection
                with rarfile.RarFile(content_path) as rar_file:
                    is_protected = rar_file.needs_password()
            elif extension == ".7z":
                # Check 7Z protection
                with py7zr.SevenZipFile(content_path, mode="r") as z7_file:
                    is_protected = z7_file.needs_password()
            else:
                is_protected = None

            return {
                "is_protected": is_protected,
                "protection_type": "password" if is_protected else None,
                "details": {},
            }

        except ImportError:
            logger.warning("Archive libraries not installed, using basic check")
            return {
                "is_protected": None,  # Unknown
                "protection_type": None,
                "details": {},
            }
        except Exception as e:
            raise ProtectedContentError(f"Error checking archive protection: {e}")

    async def _unlock_pdf(
        self,
        content_path: Path,
        password: str,
        output_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Unlock password-protected PDF.

        Args:
            content_path: Path to PDF file
            password: Password to unlock PDF
            output_path: Path to save unlocked PDF
            **kwargs: Additional options

        Returns:
            Dictionary with unlocking results
        """
        try:
            import fitz

            # Open PDF
            doc = fitz.open(content_path)

            # Check if PDF needs password
            if not doc.needs_pass:
                doc.close()
                raise ProtectedContentError("PDF is not password-protected")

            # Try to unlock with password
            if not doc.authenticate(password):
                doc.close()
                raise ProtectedContentError("Invalid PDF password")

            # Save unlocked PDF
            doc.save(output_path)
            doc.close()

            return {
                "success": True,
                "output_path": str(output_path),
            }

        except ImportError:
            raise ProtectedContentError(
                "PyMuPDF not installed, cannot unlock PDF"
            )
        except Exception as e:
            raise ProtectedContentError(f"Error unlocking PDF: {e}")

    async def _unlock_office(
        self,
        content_path: Path,
        password: str,
        output_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Unlock password-protected Office document.

        Args:
            content_path: Path to Office document
            password: Password to unlock document
            output_path: Path to save unlocked document
            **kwargs: Additional options

        Returns:
            Dictionary with unlocking results
        """
        try:
            from msoffcrypto import OfficeFile

            # Open Office document
            with open(content_path, "rb") as f:
                office_file = OfficeFile(f)

                # Check if document is protected
                if not office_file.is_encrypted():
                    raise ProtectedContentError(
                        "Office document is not password-protected"
                    )

                # Try to unlock with password
                try:
                    office_file.load_key(password=password)
                except Exception:
                    raise ProtectedContentError("Invalid Office document password")

                # Save unlocked document
                with open(output_path, "wb") as f:
                    office_file.decrypt(f)

                return {
                    "success": True,
                    "output_path": str(output_path),
                }

        except ImportError:
            raise ProtectedContentError(
                "msoffcrypto-tool not installed, cannot unlock Office document"
            )
        except Exception as e:
            raise ProtectedContentError(
                f"Error unlocking Office document: {e}"
            )

    async def _unlock_archive(
        self,
        content_path: Path,
        password: str,
        output_path: Path,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Unlock password-protected archive.

        Args:
            content_path: Path to archive file
            password: Password to unlock archive
            output_path: Path to save unlocked archive
            **kwargs: Additional options

        Returns:
            Dictionary with unlocking results
        """
        try:
            import py7zr
            import rarfile
            import zipfile

            # Get file extension
            extension = content_path.suffix.lower()

            if extension == ".zip":
                # Unlock ZIP archive
                with zipfile.ZipFile(content_path) as zip_file:
                    # Check if archive is protected
                    if not any(
                        info.flag_bits & 0x1 for info in zip_file.filelist
                    ):
                        raise ProtectedContentError(
                            "ZIP archive is not password-protected"
                        )

                    # Try to extract with password
                    try:
                        zip_file.extractall(
                            path=output_path,
                            pwd=password.encode(),
                        )
                    except Exception:
                        raise ProtectedContentError("Invalid ZIP archive password")

            elif extension == ".rar":
                # Unlock RAR archive
                with rarfile.RarFile(content_path) as rar_file:
                    # Check if archive is protected
                    if not rar_file.needs_password():
                        raise ProtectedContentError(
                            "RAR archive is not password-protected"
                        )

                    # Try to extract with password
                    try:
                        rar_file.extractall(
                            path=output_path,
                            pwd=password,
                        )
                    except Exception:
                        raise ProtectedContentError("Invalid RAR archive password")

            elif extension == ".7z":
                # Unlock 7Z archive
                with py7zr.SevenZipFile(
                    content_path,
                    mode="r",
                    password=password,
                ) as z7_file:
                    # Check if archive is protected
                    if not z7_file.needs_password():
                        raise ProtectedContentError(
                            "7Z archive is not password-protected"
                        )

                    # Try to extract with password
                    try:
                        z7_file.extractall(path=output_path)
                    except Exception:
                        raise ProtectedContentError("Invalid 7Z archive password")

            else:
                raise ProtectedContentError(
                    f"Unsupported archive type: {extension}"
                )

            return {
                "success": True,
                "output_path": str(output_path),
            }

        except ImportError:
            raise ProtectedContentError(
                "Archive libraries not installed, cannot unlock archive"
            )
        except Exception as e:
            raise ProtectedContentError(f"Error unlocking archive: {e}") 