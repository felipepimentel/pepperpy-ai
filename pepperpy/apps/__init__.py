"""Módulo de aplicações de alto nível do PepperPy.

Este módulo fornece classes de aplicação especializadas para diferentes domínios,
simplificando o desenvolvimento de aplicações de IA.

As aplicações PepperPy seguem uma arquitetura comum e fornecem interfaces
consistentes para diferentes tipos de processamento de dados e conteúdo.

Classes:
    BaseApp: Classe base para todas as aplicações PepperPy
    TextApp: Aplicação para processamento de texto
    DataApp: Aplicação para processamento de dados estruturados
    ContentApp: Aplicação para geração de conteúdo
    MediaApp: Aplicação para processamento de mídia
    RAGApp: Aplicação para Retrieval Augmented Generation
    AssistantApp: Aplicação para assistentes de IA

Example:
    >>> from pepperpy.apps import TextApp
    >>> app = TextApp("my_text_app")
    >>> app.configure(operations=["summarize", "translate"])
    >>> result = await app.process("Texto para processar")
    >>> print(result.text)
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.apps.assistant import (
    AssistantApp,
    AssistantResponse,
    Conversation,
    Message,
)
from pepperpy.apps.base import BaseApp
from pepperpy.apps.content import ContentApp, ContentResult
from pepperpy.apps.data import DataApp, DataResult
from pepperpy.apps.media import MediaApp, MediaResult
from pepperpy.apps.rag import RAGApp, RAGResult
from pepperpy.apps.text import TextApp, TextResult

__all__ = [
    "BaseApp",
    "TextApp",
    "TextResult",
    "DataApp",
    "DataResult",
    "ContentApp",
    "ContentResult",
    "MediaApp",
    "MediaResult",
    "RAGApp",
    "RAGResult",
    "AssistantApp",
    "Message",
    "Conversation",
    "AssistantResponse",
]
