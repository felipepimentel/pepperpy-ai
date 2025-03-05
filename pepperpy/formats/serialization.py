"""Serialization protocols for PepperPy.

This module defines protocols for serialization and deserialization
of objects in the PepperPy framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Protocol, Type, TypeVar, Union

T = TypeVar("T")  # Serialized type


class Serializable(Protocol):
    """Protocol for serializable objects.

    Serializable objects can be converted to and from serialized
    representations, such as dictionaries or JSON strings.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary.

        Returns:
            Dictionary representation of the object
        """
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Serializable":
        """Create an object from a dictionary.

        Args:
            data: Dictionary representation of the object

        Returns:
            New object instance
        """
        ...


class Serializer(Generic[T], ABC):
    """Abstract base class for serializers.

    Serializers convert objects to and from serialized representations.
    """

    @abstractmethod
    def serialize(self, obj: Any) -> T:
        """Serialize an object.

        Args:
            obj: Object to serialize

        Returns:
            Serialized representation of the object
        """
        pass

    @abstractmethod
    def deserialize(self, data: T, cls: Optional[Type] = None) -> Any:
        """Deserialize data to an object.

        Args:
            data: Serialized data
            cls: Optional class to deserialize to

        Returns:
            Deserialized object
        """
        pass


class JsonSerializer(Serializer[str]):
    """Serializer for JSON data.

    This serializer converts objects to and from JSON strings.
    """

    def serialize(self, obj: Any) -> str:
        """Serialize an object to a JSON string.

        Args:
            obj: Object to serialize

        Returns:
            JSON string representation of the object
        """
        import json

        if hasattr(obj, "to_dict"):
            return json.dumps(obj.to_dict())
        return json.dumps(obj)

    def deserialize(self, data: str, cls: Optional[Type] = None) -> Any:
        """Deserialize a JSON string to an object.

        Args:
            data: JSON string
            cls: Optional class to deserialize to

        Returns:
            Deserialized object
        """
        import json

        parsed = json.loads(data)
        if cls and hasattr(cls, "from_dict"):
            return cls.from_dict(parsed)
        return parsed


class DictSerializer(Serializer[Dict[str, Any]]):
    """Serializer for dictionary data.

    This serializer converts objects to and from dictionaries.
    """

    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Serialize an object to a dictionary.

        Args:
            obj: Object to serialize

        Returns:
            Dictionary representation of the object
        """
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if isinstance(obj, dict):
            return obj
        raise ValueError(f"Object of type {type(obj)} cannot be serialized to dict")

    def deserialize(self, data: Dict[str, Any], cls: Optional[Type] = None) -> Any:
        """Deserialize a dictionary to an object.

        Args:
            data: Dictionary
            cls: Optional class to deserialize to

        Returns:
            Deserialized object
        """
        if cls and hasattr(cls, "from_dict"):
            return cls.from_dict(data)
        return data
