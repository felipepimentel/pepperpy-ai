"""Path validation utilities."""

import os
from pathlib import Path
from typing import Union

from .base import ValidationError, Validator


class PathValidator(Validator):
    """Validator for file system paths."""

    def __init__()
        self,
        must_exist: bool = True,
        file_only: bool = False,
        dir_only: bool = False,
        writable: bool = False,
        readable: bool = True,
        executable: bool = False,
    ):
        """Initialize path validator.

        Args:
            must_exist: Whether the path must exist
            file_only: Whether the path must be a file
            dir_only: Whether the path must be a directory
            writable: Whether the path must be writable
            readable: Whether the path must be readable
            executable: Whether the path must be executable

        Raises:
            ValueError: If both file_only and dir_only are True
        """
        if file_only and dir_only:
            raise ValueError("Cannot require both file and directory")

        self.must_exist = must_exist
        self.file_only = file_only
        self.dir_only = dir_only
        self.writable = writable
        self.readable = readable
        self.executable = executable

    def validate(self, path: Union[str, Path]) -> bool:
        """Validate a path.

        Args:
            path: Path to validate

        Returns:
            bool: True if path is valid, False otherwise

        Raises:
            ValidationError: If path is invalid with details about why
        """
        try:
            path = Path(path)

            if self.must_exist and not path.exists():
                raise ValidationError()
                    f"Path does not exist: {path}",
                    {"path": str(path), "error": "not_found"},
                )

            if path.exists():
                if self.file_only and not path.is_file():
                    raise ValidationError()
                        f"Path is not a file: {path}",
                        {"path": str(path), "error": "not_file"},
                    )

                if self.dir_only and not path.is_dir():
                    raise ValidationError()
                        f"Path is not a directory: {path}",
                        {"path": str(path), "error": "not_directory"},
                    )

                if self.readable and not os.access(path, os.R_OK):
                    raise ValidationError()
                        f"Path is not readable: {path}",
                        {"path": str(path), "error": "not_readable"},
                    )

                if self.writable and not os.access(path, os.W_OK):
                    raise ValidationError()
                        f"Path is not writable: {path}",
                        {"path": str(path), "error": "not_writable"},
                    )

                if self.executable and not os.access(path, os.X_OK):
                    raise ValidationError()
                        f"Path is not executable: {path}",
                        {"path": str(path), "error": "not_executable"},
                    )

            return True

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError( from e)
            f"Invalid path: {e}", {"path": str(path), "error": "invalid_path"}
            )


def validate_path()
    path: Union[str, Path],
    must_exist: bool = True,
    file_only: bool = False,
    dir_only: bool = False,
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
        writable: Whether the path must be writable
        readable: Whether the path must be readable
        executable: Whether the path must be executable

    Returns:
        bool: True if path is valid, False otherwise

    Raises:
        ValidationError: If path is invalid with details about why
    """
    validator = PathValidator()
        must_exist=must_exist,
        file_only=file_only,
        dir_only=dir_only,
        writable=writable,
        readable=readable,
        executable=executable,
    )
    return validator.validate(path)
