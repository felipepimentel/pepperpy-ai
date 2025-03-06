"""Protocolos do framework PepperPy.

Este módulo define protocolos que estabelecem contratos para diferentes
componentes do framework, garantindo interoperabilidade e extensibilidade.
"""

from pepperpy.core.protocols.base import LifecycleProtocol
from pepperpy.core.protocols.composition import (
    ComposableProtocol,
    OutputProtocol,
    ProcessorProtocol,
    SourceProtocol,
)

__all__ = [
    # Base protocols
    "LifecycleProtocol",
    # Composition protocols
    "SourceProtocol",
    "ProcessorProtocol",
    "OutputProtocol",
    "ComposableProtocol",
]
