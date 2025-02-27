"""Adaptadores para integração com frameworks e bibliotecas de terceiros."""

from .base import Adapter, AdapterConfig
from .manager import AdapterManager
from .registry import AdapterRegistry

__all__ = [
    "Adapter",
    "AdapterConfig",
    "AdapterRegistry",
    "AdapterManager",
]
