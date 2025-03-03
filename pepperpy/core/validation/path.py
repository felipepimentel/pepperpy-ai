"""
Path validation utilities.
"""

import os
from pathlib import Path
from typing import Union

from pepperpy.core.errors import ValidationError


class PathValidator:
    """Validates paths with various constraints."""

    def __init__(
        self,
        must_exist: bool = True,
        file_only: bool = False,
        dir_only: bool = False,
        create_if_missing: bool = False,
        readable: bool = True,
        writable: bool = False,
        executable: bool = False,
    ):
        """Initialize with validation constraints."""
        self.must_exist = must_exist
        self.file_only = file_only
        self.dir_only = dir_only
        self.create_if_missing = create_if_missing
        self.readable = readable
        self.writable = writable
        self.executable = executable

        # Validate constraints
        if self.file_only and self.dir_only:
            raise ValueError("Cannot set both file_only and dir_only to True")

    def validate(self, path: Union[str, Path]) -> bool:
        """Validate a path against the constraints.

        Args:
            path: Path to validate

        Returns:
            True if path is valid

        Raises:
            ValidationError: If path does not meet constraints

        """
        try:
            # Convert to Path object
            if isinstance(path, str):
                path = Path(path)

            # Check if path exists
            if not path.exists():
                if self.must_exist:
                    if self.create_if_missing:
                        if self.dir_only:
                            path.mkdir(parents=True, exist_ok=True)
                        elif self.file_only:
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.touch()
                        else:
                            # Default to file
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.touch()
                    else:
                        raise ValidationError(
                            f"Path does not exist: {path}",
                            {"path": str(path), "error": "not_found"},
                        )
                return True

            # Check if path is a file or directory
            if self.file_only and not path.is_file():
                raise ValidationError(
                    f"Path is not a file: {path}",
                    {"path": str(path), "error": "not_file"},
                )

            if self.dir_only and not path.is_dir():
                raise ValidationError(
                    f"Path is not a directory: {path}",
                    {"path": str(path), "error": "not_directory"},
                )

            # Check permissions
            if self.readable and not os.access(path, os.R_OK):
                raise ValidationError(
                    f"Path is not readable: {path}",
                    {"path": str(path), "error": "not_readable"},
                )

            if self.writable and not os.access(path, os.W_OK):
                raise ValidationError(
                    f"Path is not writable: {path}",
                    {"path": str(path), "error": "not_writable"},
                )

            if self.executable and not os.access(path, os.X_OK):
                raise ValidationError(
                    f"Path is not executable: {path}",
                    {"path": str(path), "error": "not_executable"},
                )

            return True

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                f"Invalid path: {e}",
                {"path": str(path), "error": "invalid_path"},
            ) from e


def validate_path(
    path: Union[str, Path],
    must_exist: bool = True,
    file_only: bool = False,
    dir_only: bool = False,
    create_if_missing: bool = False,
    writable: bool = False,
    readable: bool = True,
    executable: bool = False,
) -> bool:
    """Validate a path with given constraints.

    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        file_only: Whether the path must be a file
        dir_only: Whether the path must be a directory
        create_if_missing: Whether to create the path if it doesn't exist
        writable: Whether the path must be writable
        readable: Whether the path must be readable
        executable: Whether the path must be executable

    Returns:
        True if path is valid

    Raises:
        ValidationError: If path does not meet constraints

    """
    validator = PathValidator(
        must_exist=must_exist,
        file_only=file_only,
        dir_only=dir_only,
        create_if_missing=create_if_missing,
        writable=writable,
        readable=readable,
        executable=executable,
    )
    return validator.validate(path)
