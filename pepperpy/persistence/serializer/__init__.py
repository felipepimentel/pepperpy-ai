"""Serializer module for Pepperpy framework.

This module provides serialization implementations for different
data formats and protocols.
"""

from pepperpy.persistence.serializer.base import BaseSerializer, SerializerError

__all__ = [
    "BaseSerializer",
    "SerializerError",
] 