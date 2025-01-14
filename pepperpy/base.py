"""Base module for data classes and protocols."""

from dataclasses import asdict, dataclass
from typing import Any, ClassVar, TypeVar

T = TypeVar("T", bound="BaseData")


@dataclass
class BaseData:
    """Base data class with serialization support."""

    # Class variables
    _exclude_fields: ClassVar[set[str]] = set()

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert to dictionary.

        Args:
            exclude: Optional set of field names to exclude from the dictionary.

        Returns:
            Dictionary representation with optional field exclusion.
        """
        exclude_set = exclude or set()
        exclude_set.update(self._exclude_fields)

        data = asdict(self)
        return {k: v for k, v in data.items() if k not in exclude_set and v is not None}

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create instance from dictionary.

        Args:
            data: Dictionary containing instance data.

        Returns:
            Instance of this class.

        Example:
            >>> data = {"field": "value"}
            >>> instance = BaseData.from_dict(data)
        """
        # Filter out unknown fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def update(self, **kwargs: Any) -> None:
        """Update instance fields with new values.

        Args:
            **kwargs: Field names and values to update.

        Example:
            >>> instance.update(field="new_value")
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Get string representation.

        Returns:
            String representation of the instance.
        """
        fields = [f"{k}={v!r}" for k, v in self.to_dict().items()]
        return f"{self.__class__.__name__}({', '.join(fields)})"
