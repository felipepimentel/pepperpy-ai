"""Base module."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class BaseData:
    """Base data class."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseData":
        """Create from dictionary.

        Args:
            data: Dictionary data.

        Returns:
            Instance of this class.
        """
        return cls(**data)
