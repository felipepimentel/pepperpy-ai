"""Módulo de fontes de dados do PepperPy.

Este módulo fornece classes para acesso e processamento de diferentes
fontes de dados, como arquivos, APIs, bancos de dados, etc.

As fontes de dados PepperPy seguem uma interface comum e fornecem
métodos assíncronos para leitura e escrita de dados de diferentes origens.

Classes:
    BaseSource: Classe base para todas as fontes de dados
    SourceConfig: Configuração para fontes de dados
    FileSource: Fonte de dados baseada em arquivo binário
    TextFileSource: Fonte de dados baseada em arquivo de texto
    JSONFileSource: Fonte de dados baseada em arquivo JSON
    WebSource: Fonte de dados baseada em recursos web
    WebAPISource: Fonte de dados baseada em API web
    RSSSource: Fonte de dados baseada em feed RSS

Example:
    >>> from pepperpy.core.sources import JSONFileSource
    >>> source = JSONFileSource("data.json")
    >>> async with source:
    ...     data = await source.read()
    >>> print(data)

    >>> from pepperpy.core.sources import WebAPISource
    >>> api = WebAPISource("https://api.example.com/data")
    >>> async with api:
    ...     result = await api.read(method="GET", params={"limit": 10})
    >>> print(result)
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.core.sources.base import BaseSource, SourceConfig
from pepperpy.core.sources.file import FileSource, JSONFileSource, TextFileSource
from pepperpy.core.sources.rss import RSSSource
from pepperpy.core.sources.web import WebAPISource, WebSource

__all__ = [
    "BaseSource",
    "SourceConfig",
    "FileSource",
    "TextFileSource",
    "JSONFileSource",
    "WebSource",
    "WebAPISource",
    "RSSSource",
]
