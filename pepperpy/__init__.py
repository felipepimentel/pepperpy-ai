"""PepperPy: Framework para desenvolvimento de aplicações de IA.

PepperPy é um framework Python para desenvolvimento de aplicações
de IA com foco em produtividade, modularidade e extensibilidade.

O framework PepperPy fornece componentes para:
- Aplicações especializadas para diferentes domínios (texto, dados, conteúdo, mídia, RAG, assistentes)
- Fontes de dados para acesso a diferentes origens (arquivos, web, APIs, RSS)
- Composição funcional para criação de pipelines de processamento
- Abstração por intenção para expressar operações de forma natural
- Templates pré-configurados para casos de uso comuns
- Assistência ao desenvolvedor para diagnóstico e otimização
- Integração multimodal para trabalhar com diferentes tipos de dados
- Workflows adaptativos para aprendizado incremental

Módulos Principais:
    pepperpy.core: Componentes fundamentais e infraestrutura básica
    pepperpy.multimodal: Processamento multimodal (texto, imagem, áudio, vídeo)
    pepperpy.workflows: Fluxos de trabalho e orquestração
    pepperpy.agents: Agentes inteligentes e assistentes
    pepperpy.rag: Retrieval Augmented Generation
    pepperpy.llm: Integração com modelos de linguagem
    pepperpy.embedding: Embeddings e representações vetoriais

Example:
    >>> import pepperpy as pp
    >>> from pepperpy.core.apps import TextApp
    >>> app = TextApp("my_text_app")
    >>> app.configure(operations=["summarize", "translate"])
    >>> result = await app.process("Texto para processar")
    >>> print(result.text)

    >>> from pepperpy.core.sources import JSONFileSource
    >>> source = JSONFileSource("data.json")
    >>> async with source:
    ...     data = await source.read()
    >>> print(data)
"""

from typing import Any, Dict, List, Optional, Union

# Aplicações
from pepperpy.core.apps import (
    AssistantApp,
    AssistantResponse,
    BaseApp,
    ContentApp,
    ContentResult,
    Conversation,
    DataApp,
    DataResult,
    MediaApp,
    MediaResult,
    Message,
    RAGApp,
    RAGResult,
    TextApp,
    TextResult,
)

# Fontes de dados
from pepperpy.core.sources import (
    BaseSource,
    FileSource,
    JSONFileSource,
    RSSSource,
    SourceConfig,
    TextFileSource,
    WebAPISource,
    WebSource,
)

# Multimodal
from pepperpy.multimodal import (
    BaseModalityConverter,
    ImageToTextConverter,
    Modality,
    ModalityConverter,
    ModalityData,
    TextToImageConverter,
    convert_between_modalities,
)

# Workflows adaptativos
from pepperpy.workflows.adaptive import (
    AdaptiveWorkflow,
    FeedbackCollector,
    FeedbackProcessor,
)

__version__ = "0.1.0"

__all__ = [
    # Aplicações
    "BaseApp",
    "TextApp",
    "DataApp",
    "ContentApp",
    "MediaApp",
    "RAGApp",
    "AssistantApp",
    "TextResult",
    "DataResult",
    "ContentResult",
    "MediaResult",
    "RAGResult",
    "Message",
    "Conversation",
    "AssistantResponse",
    # Fontes de dados
    "BaseSource",
    "SourceConfig",
    "FileSource",
    "TextFileSource",
    "JSONFileSource",
    "WebSource",
    "WebAPISource",
    "RSSSource",
    # Multimodal
    "Modality",
    "ModalityData",
    "ModalityConverter",
    "BaseModalityConverter",
    "convert_between_modalities",
    "TextToImageConverter",
    "ImageToTextConverter",
    # Workflows adaptativos
    "AdaptiveWorkflow",
    "FeedbackCollector",
    "FeedbackProcessor",
]
